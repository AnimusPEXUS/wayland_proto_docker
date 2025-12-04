import os.path
import sys

import functools
import getopt
import json

import yaml

import lxml.etree

from lxml.builder import E as LBE


# from yaml import load, dump
# from yaml import Loader, Dumper

DATA_TYPES = [
    'int', 'uint', 'fixed', 'object',
    'new_id', 'string', 'array', 'fd', 'enum' 
]

STABILITY_ORDER = ['stable', 'staging', 'unstable', 'unknown']

KNOWN_STABLE = ['wayland.xml']
KNOWN_STAGING = []
KNOWN_UNSTABLE = []

PREDEFINED_ORDER = ['wayland.xml']

CPP_DISABLE_TEXTS = True


def apply_common_fields_to_object_from_element(obj, element):

    obj.name = element.get('name', '')

    descr_os = []

    descrs = element.xpath('description')

    for descr in descrs:
        t = descr.text
        if t is None:
            t = ""
        d = Description()
        d.text = t.strip()
        d.summary = descr.get('summary', '').strip()

        descr_os.append(d)

    obj.descriptions = descr_os

    copy_os = []

    copys = element.xpath('copyright')

    for copy in copys:
        t = copy.text
        if t is None:
            t = ""
        d = Copyright()
        d.text = t.strip()
        d.name = ''

        copy_os.append(d)

    obj.copyrights = copy_os


def gen_descriptions_html(descriptions):

    descriptions_div = LBE.div('')

    for descr in descriptions:
        descriptions_div.append(
            LBE.div(
                LBE.div('summary: ', descr.summary),
                LBE.div('description: ', descr.text,
                        {'class': 'description-div'})
            )
        )
    return descriptions_div


def gen_messages_html(messages, toc, idname_2, mode='requests'):

    single_txt = 'request'
    short_txt = 'req'
    if mode == 'requests':
        pass
    elif mode == 'events':
        single_txt = 'event'
        short_txt = 'eve'
    elif mode == 'enums':
        single_txt = 'enum'
        short_txt = 'enu'
    else:
        raise RuntimeError("invalid 'mode' arg")

    multiple_txt = '{}s'.format(single_txt)

    messages_div = LBE.div('', {'class': multiple_txt+'-div'})
    for message in messages:

        n = message.name
        idname_3 = idname_2 + '-'+short_txt+'-' + n

        toc.append(LBE.div({'class': 'level3'}, LBE.a(
            {'href': '#'+idname_3}, short_txt+': '+n)))

        message_div = LBE.div(
            single_txt+": ",
            LBE.b(
                message.name,
                {'class': single_txt+'-name'}
            ),
            {'id': idname_3}
        )

        message_div.append(gen_descriptions_html(message.descriptions))

        if mode in ['requests', 'events']:
            args = message.arguments
            if len(args) > 0:
                args_table = LBE.table(
                    LBE.tr(
                        LBE.th('arg name'),
                        LBE.th('type'),
                        LBE.th('interface'),
                        LBE.th('summary'),
                    ),
                    {'class': 'args-table'}
                )
                for arg in args:
                    arg_row = LBE.tr(
                        LBE.td(LBE.b(arg.name, {'class': 'arg-name'})),
                        LBE.td(arg.type_),
                        LBE.td(arg.interface),
                        LBE.td(arg.summary),
                    )
                    args_table.append(arg_row)

                message_div.append(args_table)
        else:
            args = message.entries
            if len(args) > 0:
                args_table = LBE.table(
                    LBE.tr(
                        LBE.th('entry name'),
                        LBE.th('value'),
                        LBE.th('summary'),
                    ),
                    {'class': 'args-table'}
                )
                for arg in args:
                    arg_row = LBE.tr(
                        LBE.td(LBE.b(arg.name, {'class': 'arg-name'})),
                        LBE.td(arg.value),
                        LBE.td(arg.summary),

                    )
                    args_table.append(arg_row)

                message_div.append(args_table)

        messages_div.append(message_div)
    return messages_div


def apply_args_to_object(obj, element):
    args = element.xpath('arg')
    for arg in args:
        arg_o = Argument()
        arg_o.name = arg.get('name', '')
        arg_o.type_ = arg.get('type', '')
        arg_o.interface = arg.get('interface', '')
        arg_o.summary = arg.get('summary', '')

        obj.arguments.append(arg_o)


def arguments_simple_struct(requset_or_event):

    ret = []

    for arg in requset_or_event.arguments:

        arg_value = []

        arg_value.append(['name', arg.name])
        arg_value.append(['type', arg.type_])
        arg_value.append(['interface', arg.interface])
        arg_value.append(['summary', arg.summary])

        ret.append(arg_value)

    return ret


def entries_simple_struct(enum):

    ret = []

    for entry in enum.entries:

        entry_value = []

        entry_value.append(['name', entry.name])
        entry_value.append(['value', entry.value])
        entry_value.append(['summary', entry.summary])

        ret.append(entry_value)

    return ret


def common_fields_from_obj_to_simple_struct(lst, obj):
    lst.append(['name', obj.name])
    descriptions = []
    for i in obj.descriptions:
        descriptions.append([i.summary, i.text])
    lst.append(['descriptions', descriptions])


class Copyright:

    def __init__(self):
        self.name = ''
        self.text = ''

    def gen_cpp(self):
        n = ""
        t = ""

        if not CPP_DISABLE_TEXTS:
            n = self.name
            t = self.text

        return '''
        Copyright{
           .name="'''+n+'''",
           .text=R"+++('''+t+''')+++"
        }
        '''


class Description:

    def __init__(self):
        self.text = ''
        self.summary = ''

    def gen_cpp(self):
        s = ""
        t = ""

        if not CPP_DISABLE_TEXTS:
            s = self.summary
            t = self.text

        return '''
        Description{
           .summary=R"+++('''+s+''')+++",
           .text=R"+++('''+t+''')+++"
           }
           '''


class CommonFields:

    def __init__(self):
        self.name = ''
        self.descriptions = []
        self.copyrights = []

    def gen_cpp(self):

        descriptions_code_lst = []

        for i in self.descriptions:
            descriptions_code_lst.append(i.gen_cpp())

        descriptions_code = ','.join(descriptions_code_lst)

        copyrights_code_lst = []

        for i in self.copyrights:
            copyrights_code_lst.append(i.gen_cpp())

        copyrights_code = ','.join(copyrights_code_lst)

        ret = '''
CommonFields{
        .name="'''+self.name+'''",
        .descriptions={'''+descriptions_code+'''},
        .copyrights={'''+copyrights_code+'''}
    }
'''
        return ret


class ProtocolCollection:

    def __init__(self):
        self.protocol_files = []

    def getProtoByName(self, name):
        ret = []
        for i in self.protocol_files:
            for j in i:
                if j.name == name:
                    ret.append(j)
        return ret

    def sort_protocol_files(self):
        self.protocol_files.sort(
            key=functools.cmp_to_key(self._protocol_files_sorter))

    def _protocol_files_sorter(self, v1, v2):
        if v1.basename in PREDEFINED_ORDER and v2.basename in PREDEFINED_ORDER:
            i1 = PREDEFINED_ORDER.index(v1.basename)
            i2 = PREDEFINED_ORDER.index(v2.basename)
            if i1 == i2:
                return 0
            elif i1 > i2:
                return 1
            else:
                return -1

        elif v1.basename in PREDEFINED_ORDER and v2.basename not in PREDEFINED_ORDER:
            return -1
        elif v1.basename not in PREDEFINED_ORDER and v2.basename in PREDEFINED_ORDER:
            return 1

        else:

            s1 = STABILITY_ORDER.index(v1.calc_stability())
            s2 = STABILITY_ORDER.index(v2.calc_stability())

            if s1 > s2:
                return 1
            elif s1 < s2:
                return -1

            else:

                if v1.basename > v2.basename:
                    return 1
                elif v1.basename < v2.basename:
                    return -1
                else:
                    return 0

    def gen_cpp(self):

        protocol_files_lst = []
        for i in self.protocol_files:
            protocol_files_lst.append(i.gen_cpp())

        protocol_files_txt = ','.join(protocol_files_lst)

        ret = '''
const ProtocolCollection WAYLAND_PROTOCOL_COLLECTION =
{
   .protocol_files = {
''' + protocol_files_txt + '''
   }
};
'''
        return ret


class ProtocolFile(CommonFields):

    # TODO: read common fields from xml
    # TODO: write common fields to outputs

    def __init__(self):
        super().__init__()
        self.basename = ''
        self.dirname = ''
        self.protocols = []

    def calc_stability(self):
        if self.basename in KNOWN_STABLE:
            return 'stable'

        if self.basename in KNOWN_STAGING:
            return 'staging'

        if self.basename in KNOWN_UNSTABLE:
            return 'unstable'

        splitted = self.dirname.split('/')

        if 'stable' in splitted:
            return 'stable'

        if 'unstable' in splitted:
            return 'unstable'

        if 'staging' in splitted:
            return 'staging'

        return 'unknown'

    def gen_cpp(self):

        protocols_code = ''
        protocols_code_lst = []

        for i in self.protocols:
            protocols_code_lst.append(i.gen_cpp())

        protocols_code = ','.join(protocols_code_lst)

        del protocols_code_lst

        ret = '''

        {
        '''+super().gen_cpp()+''',
        "'''+self.basename+'''",
        "'''+self.dirname+'''",
        {'''+protocols_code+'''}
        }


'''

        return ret


class Protocol(CommonFields):

    def __init__(self):
        super().__init__()
        # self.status = 'unstable'
        self.interfaces = []

    def gen_cpp(self):

        interfaces_code_list = []

        for i in self.interfaces:
            interfaces_code_list.append(i.gen_cpp())

        interfaces_code = ','.join(interfaces_code_list)

        ret = '''
        Protocol(
            '''+super().gen_cpp()+''',
            {'''+interfaces_code+'''}
            )
'''
        #

        return ret


class Interface(CommonFields):

    def __init__(self):
        super().__init__()
        self.version = '0'
        self.requests = []
        self.events = []
        self.enums = []

    def gen_cpp(self):

        requests_code_list = []
        events_code_list = []
        enums_code_list = []

        for i in self.requests:
            requests_code_list.append(i.gen_cpp())

        for i in self.events:
            events_code_list.append(i.gen_cpp())

        for i in self.enums:
            enums_code_list.append(i.gen_cpp())

        requests_code = ','.join(requests_code_list)
        events_code = ','.join(events_code_list)
        enums_code = ','.join(enums_code_list)

        ret = '''
        Interface(
        '''+super().gen_cpp()+''',
        "'''+self.version+'''",
        {'''+requests_code+'''},
        {'''+events_code+'''},
        {'''+enums_code+'''}
        )
'''

        return ret


class Message(CommonFields):

    def __init__(self):
        super().__init__()
        self.arguments = []

    def gen_cpp(self):

        arguments_code_list = []

        for i in self.arguments:
            arguments_code_list.append(i.gen_cpp())

        arguments_code = ','.join(arguments_code_list)

        ret = '''
        Message(
            '''+super().gen_cpp()+''',
            {'''+arguments_code+'''}
            )
'''
        return ret


class Request(Message):
    def __init__(self):
        super().__init__()


class Event(Message):
    def __init__(self):
        super().__init__()


class Argument:

    def __init__(self):
        self.name = ''
        self.type_ = ''
        self.interface = ''
        self.summary = ''

    def gen_cpp(self):

        type_txt = 'wt_'+self.type_

        summary = ""
        if not CPP_DISABLE_TEXTS:
            summary = self.summary

        return '''
        Argument{
        .name="'''+self.name+'''",
        .type='''+type_txt+''',
        .interface="'''+self.interface+'''",
        .summary="'''+summary+'''",
        }
        '''


class Enum(CommonFields):

    def __init__(self):
        super().__init__()
        self.entries = []

    def gen_cpp(self):
        entries_code_list = []

        for i in self.entries:
            entries_code_list.append(i.gen_cpp())

        entries_code = ','.join(entries_code_list)

        ret = '''
        Enum(
            '''+super().gen_cpp()+''',
            {'''+entries_code+'''}
            )
'''
        return ret


class Entry:
    def __init__(self):
        self.name = ''
        self.value = ''
        self.summary = ''

    def gen_cpp(self):

        summary = ""
        if not CPP_DISABLE_TEXTS:
            summary = self.summary

        return '''
        Entry{
        .name="'''+self.name+'''",
        .value="'''+self.value+'''",
        .summary="'''+summary+'''",
        }
        '''


def parse_xml(filename):

    filename = os.path.abspath(filename)

    dirname = os.path.relpath(
        os.path.dirname(filename),
        os.path.dirname(
            os.path.abspath(sys.argv[0])
        )
    )
    basename = os.path.basename(filename)

    key_name = '{}/{}'.format(dirname, basename)

    parsed = None

    try:
        with open(filename, 'rb') as f:
            txt = f.read()
            parsed = lxml.etree.fromstring(txt)
    except Exception as e:
        print("can't open, read and/or parse file. error: {}".format(e))
        print("^^^^ skipping ^^^^: {}".format(filename))
        return None, None

    protocol = parsed.xpath('/protocol')

    if len(protocol) == 0:
        return None, None

    parsed_info = dict()
    # parsed_info['name'] = proto_name
    parsed_info['dirname'] = dirname
    parsed_info['basename'] = basename
    parsed_info['parsed'] = parsed

    return key_name, parsed_info


def find_all_xml_files(dirname):

    ret = []

    dirname = os.path.abspath(dirname)

    dirs_to_check = []
    dirs_to_check.append('.')

    while len(dirs_to_check) != 0:
        d = dirs_to_check.pop(0)

        dirfiles = os.listdir(os.path.join(dirname, d))

        for i in dirfiles:

            r_path = os.path.join(d, i)
            a_path = os.path.join(dirname, r_path)

            if os.path.isdir(a_path) and not os.path.islink(a_path):
                dirs_to_check.append(r_path)
                continue

            if os.path.isfile(a_path) and not os.path.islink(a_path):
                if i.endswith('.xml'):
                    ret.append(r_path)
                continue

    return ret


def generate_html_for_ProtocolCollection(protocol_collection, toc, super_toc):

    proto_collection_div = LBE.div('')

    for proto_file in protocol_collection.protocol_files:

        proto_file_div = LBE.div('')
        proto_collection_div.append(proto_file_div)

        for protocol in proto_file.protocols:

            idname_1 = protocol.name
            super_idname_1 = 'superid-'+idname_1

            toc.append(
                LBE.div(
                    {
                        'class': 'level1',
                        'id': super_idname_1
                    },
                    LBE.a(
                        {
                            'href': '#'+idname_1
                        },
                        'p: '+idname_1
                    )
                )
            )

            super_toc.append(
                LBE.div(
                    {
                        'class': 'level1',
                    },
                    LBE.a(
                        {
                            'href': '#'+super_idname_1
                        },
                        idname_1
                    )
                )
            )

            protocol_div = lxml.etree.Element(
                'div', {'id': idname_1, 'class': 'protocol-div'})
            proto_file_div.append(protocol_div)
            protocol_div_name = LBE.div('{}'.format(protocol.name), {
                                        'class': 'protocol-name'})
            protocol_div.append(protocol_div_name)
            protocol_div.append(
                LBE.div(
                    "protocol file: {} ; dirname: {}".format(
                        proto_file.basename,
                        proto_file.dirname
                    )
                )
            )

            interfaces_div = lxml.etree.Element('div')
            interfaces_div_txt = LBE.div(
                '{} interface(s)'.format(len(protocol.interfaces)))
            interfaces_div.append(interfaces_div_txt)

            for interface in protocol.interfaces:

                n = interface.name
                idname_2 = idname_1 + '-'+n

                toc.append(LBE.div({'class': 'level2'}, LBE.a(
                    {'href': '#'+idname_2}, 'i: '+n)))

                interface_div = LBE.div(
                    '', {'id': idname_2, 'class': 'interface-div'})
                interface_div.append(
                    LBE.div(
                        'interface: ', LBE.b(interface.name, {
                                             'class': "interface-name"}),
                        ', version: ', LBE.b(interface.version),
                        {"class": "interface-title"}
                    )
                )

                interface_div.append(
                    gen_descriptions_html(interface.descriptions))

                if len(interface.requests) > 0:
                    interface_div.append(
                        gen_messages_html(
                            interface.requests,
                            toc,
                            idname_2
                        )
                    )

                if len(interface.events) > 0:
                    interface_div.append(
                        gen_messages_html(
                            interface.events,
                            toc,
                            idname_2,
                            mode='events'
                        )
                    )

                if len(interface.enums) > 0:
                    interface_div.append(
                        gen_messages_html(
                            interface.enums,
                            toc,
                            idname_2,
                            mode='enums'
                        )
                    )

                interfaces_div.append(interface_div)

            protocol_div.append(interfaces_div)

    return proto_collection_div


def generate_ProtocolCollection(parsed_docs):

    # stable, staging, unstable = stable_unstable_sort(parsed_docs)

    ret = ProtocolCollection()

    for i in parsed_docs:
        pf = generate_ProtocolFile_for_parsed(parsed_docs[i])
        if pf is not None:
            ret.protocol_files.append(pf)

    return ret


def generate_ProtocolFile_for_parsed(parsed_info):

    protocol_file = ProtocolFile()
    protocol_file.basename = parsed_info['basename']
    protocol_file.dirname = parsed_info['dirname']

    protocols = parsed_info['parsed'].xpath('/protocol')

    if len(protocols) == 0:
        return None

    for protocol in protocols:

        prot_o = Protocol()

        apply_common_fields_to_object_from_element(prot_o, protocol)

        # prot_o.status=parsed_info['status']

        interfaces = protocol.xpath('interface')

        for interface in interfaces:

            interf_o = Interface()

            apply_common_fields_to_object_from_element(interf_o, interface)

            interf_o.version = interface.get('version', '0')

            interf_o.requests = []
            interf_o.events = []
            interf_o.enums = []

            requests = interface.xpath('request')
            for request in requests:
                request_o = Request()
                apply_common_fields_to_object_from_element(
                    request_o, request)
                apply_args_to_object(request_o, request)
                interf_o.requests.append(request_o)

            events = interface.xpath('event')
            for event in events:
                event_o = Event()
                apply_common_fields_to_object_from_element(event_o, event)
                apply_args_to_object(event_o, event)
                interf_o.events.append(event_o)

            enums = interface.xpath('enum')
            for enum in enums:
                enum_o = Enum()

                apply_common_fields_to_object_from_element(enum_o, enum)

                entrys = enum.xpath('entry')
                for entry in entrys:
                    entry_o = Entry()
                    entry_o.name = entry.get('name', '')
                    entry_o.value = entry.get('value', '')
                    entry_o.summary = entry.get('summary', '')

                    enum_o.entries.append(entry_o)

                interf_o.enums.append(enum_o)

            prot_o.interfaces.append(interf_o)

        protocol_file.protocols.append(prot_o)

    return protocol_file


def generate_simple_struct(list_of_Protocols):

    # note: here are intentionally used list of tuples and not OrderedDict.
    #       order is important in wayland's requests, events and arguments

    proto_od = []

    for protocol_file in list_of_Protocols.protocol_files:

        proto_file_tuple_list = []
        proto_od.append(['protocol_file', proto_file_tuple_list])

        proto_file_tuple_list.append(['basename', protocol_file.basename])
        proto_file_tuple_list.append(['dirname', protocol_file.dirname])

        protos_tuple_list = []
        proto_file_tuple_list.append(['protocols', protos_tuple_list])

        for protocol in protocol_file.protocols:

            proto_tuple_list = []
            protos_tuple_list.append(proto_tuple_list)

            common_fields_from_obj_to_simple_struct(proto_tuple_list, protocol)

            # proto_tuple_list.append(['status', protocol.status])

            interfs_tuple_list = []
            proto_tuple_list.append(['interfaces', interfs_tuple_list])

            for interface in protocol.interfaces:

                interf_tuple_list = []
                common_fields_from_obj_to_simple_struct(
                    interf_tuple_list, interface)

                interf_tuple_list.append(['version', interface.version])

                # work with requests

                reqs_tuple_list = []
                interf_tuple_list.append(['requests', reqs_tuple_list])

                for request in interface.requests:

                    req_tuple_list = []
                    common_fields_from_obj_to_simple_struct(
                        req_tuple_list, request)

                    req_tuple_list.append(
                        ['args', arguments_simple_struct(request)])

                    reqs_tuple_list.append(req_tuple_list)

                # work with events

                eves_tuple_list = []
                interf_tuple_list.append(['events', eves_tuple_list])

                for event in interface.events:

                    eve_tuple_list = []
                    common_fields_from_obj_to_simple_struct(
                        eve_tuple_list, event)

                    eve_tuple_list.append(
                        ['args', arguments_simple_struct(event)])

                    eves_tuple_list.append(eve_tuple_list)

                # work with enums

                enus_tuple_list = []
                interf_tuple_list.append(['enums', enus_tuple_list])

                for enum in interface.enums:

                    enu_tuple_list = []
                    common_fields_from_obj_to_simple_struct(
                        enu_tuple_list, enum)

                    enu_tuple_list.append(
                        ['entries', entries_simple_struct(enum)])

                    enus_tuple_list.append(enu_tuple_list)

                # end of works

                interfs_tuple_list.append(interf_tuple_list)

    return proto_od


def generate_yaml(simple_struct):
    ret = yaml.dump(simple_struct, Dumper=yaml.Dumper)
    return ret


def generate_json(simple_struct):
    ret = json.dumps(simple_struct, indent=4)
    return ret


def generate_html(obj_tree):

    # stable, staging, unstable = stable_unstable_sort(parsed_docs)

    # sorted_proto_name_list = gen_sorted_proto_name_list(parsed_docs)

    texts = ''

    body = lxml.etree.Element('body')
    main_div = LBE.div('', {'id': 'main-div'})
    toc = LBE.div('', {'id': 'toc-div'})
    super_toc = LBE.div('', {'id': 'supertoc-div'})
    body.append(super_toc)
    body.append(toc)
    body.append(main_div)

    main_div.append(
        generate_html_for_ProtocolCollection(obj_tree, toc, super_toc)
    )

    html_struct = LBE.html(
        LBE.head(
            LBE.title("Wayland Protocols Documentation"),
            LBE.style('''
            body { font-size: 10px; font-family: "Go Mono"; margin: 0; padding: 0;}
            #main-div {
                position: absolute;
                left: 210px;
                right: 210px;
                top: 0px;
                bottom: 0px;
                overflow: scroll;
                padding-left: 20px;
                padding-right: 20px;
                }
            #main-div table { font-size: 10px; font-family: "Go Mono"; }
            #main-div div {  }
            #supertoc-div {
                   position: fixed;
                   top: 0px; left: 0px; bottom: 0px; width: 200px;
                   overflow: scroll; padding-top: 20px; padding-bottom: 20px;
                   text-wrap: nowrap;white-space: nowrap;
                   border: 5px black dotted;
                }
            #toc-div {
                   position: fixed;
                   top: 0px; right: 0px; bottom: 0px; width: 200px;
                   overflow: scroll; padding-top: 20px; padding-bottom: 20px;
                   text-wrap: nowrap;white-space: nowrap;
                   border: 5px black dotted;
                }
            #toc-div .level1 {margin-left: 0px; margin-top: 10px; }
            #toc-div .level2 {margin-left: 10px; margin-top: 5px;  }
            #toc-div .level3 {margin-left: 20px; }
            #toc-div .level1 a {color: red;}
            #toc-div .level2 a {color: teal;}
            #toc-div .level3 a {color: maroon;}
            .protocol-name {
               font-size: 20px;
               border: 3px solid black;
               border-radius: 5px;
               padding: 5px;
               margin: 0 !important;
            }
            .protocol-div div {margin-left: 10px;}
            .interface-name {color: green;}
            .request-name, .event-name, .enum-name {color: maroon; font-size: 13px;}
            .requests-div, .events-div, .enums-div {border: 2px solid silver; box-shadow: 2px 2px 0px gold; padding-bottom: 10px; margin-bottom: 5px;}
            .interface-title { color: blue; }
            .interface-div { margin-bottom: 5px; border: 1px gray dotted; padding: 5px; border-radius: 5px;}
            .description-div { color: grey; padding: 2px; padding-left: 20px; padding-right: 20px; border: 1px grey dotted; text-align: justify; margin-left: 20px; margin-bottom:5px;}
            .args-table { margin-left: 20px; /* width: 100%; */ }
            .args-table td { padding-left: 10px; padding-right: 10px; border: 1px gray solid; box-shadow: 2px 2px 0px teal;}
            .args-table th { text-align: left; }
            .arg-name { }

            '''),
        ),
        body
    )

    ret = lxml.etree.tostring(
        html_struct,
        pretty_print=True,
        method='html'
    )

    return ret


def generate_cpp_code(obj_tree):

    # TODO: add generation timestamp

    ret = '''#ifndef WAYROUND_I2P_20240211_135005_438825
#define WAYROUND_I2P_20240211_135005_438825

namespace wayround_i2p::waylandcc {
    
/*
    WARNING! This file GENERTED using
             https://github.com/AnimusPEXUS/wayland_proto_docker
             tool.
*/

''' + obj_tree.gen_cpp() + '''

}

#endif
'''
    return ret


def print_help():
    print(
        """
{cmd} [options] target

  recurcively searches for .xml files in current directory and trying to
  find wayland protocols in them.

  -o  filename    - where to store. if omitted - generated automatically

  valid targets:

     html      - (default) generates index.html with /readabale/ documentation

     yaml      - generates yaml document with yaml representation
                 of all found .xml protocols

     json      - same as yaml, but generates json

     c++       - generates C++ .hpp include file
                 to be included in waylandcc project
                 (see https://github.com/AnimusPEXUS/waylandcc).
""".format(cmd=sys.argv[0]))


def main():

    argv = sys.argv
    len_argv = len(argv)

    if len_argv == 0:
        raise RuntimeError("invalid sys.argv")

    if argv[0] == '-c':
        raise RuntimeError("this must be run as script")

    opts, args = getopt.getopt(argv[1:], 'o:h', ['help'])

    output = ''
    for i in opts:
        if i[0] == '-o:':
            output = i[1]
        if i[0] in ['-h', '--help']:
            print_help()
            return

    target = args[0]

    acceptable_targets = ['html', 'yaml', 'json', 'c++']

    if not target in acceptable_targets:
        raise RuntimeError(
            "invalid target. valid are {}".format(acceptable_targets))

    if output == '':
        if target == 'html':
            output = 'index.html'
        elif target == 'yaml':
            output = 'wayland-protocols.yaml'
        elif target == 'json':
            output = 'wayland-protocols.json'
        elif target == 'c++':
            output = 'wayland_protocol_generated.hpp'
        else:
            raise RuntimeError("invalid target")

    print(f"target is {target}. output file is {output}")

    if len(args) != 1:
        raise RuntimeError("invalid arg count")

    cwd = os.path.dirname(os.path.abspath(argv[0]))

    xml_files = find_all_xml_files(cwd)

    print("found {} xml files".format(len(xml_files)))

    print("parsing xml..")
    parsed_docs = dict()
    for i in xml_files:
        print(f"  {i}: ", end='')
        i = os.path.join(cwd, i)
        k, v = parse_xml(i)
        if k is None or v is None:
            print("  fail")
            continue

        k_spl = k.split('/')
        if 'tests' in k_spl:
            print("  fail")
            continue

        print("  ok")
        parsed_docs[k] = v

    print("parsing result: {} protocol files".format(len(parsed_docs)))

    print("generating tree..")
    obj_tree = generate_ProtocolCollection(parsed_docs)

    print("sorting..")
    obj_tree.sort_protocol_files()

    del parsed_docs

    if target == 'html':
        print("generating html")

        txt = generate_html(obj_tree)

        with open(output, 'wb') as f:
            f.write(txt)

    elif target == 'yaml':
        print("generating yaml")

        struct = generate_simple_struct(obj_tree)

        txt = generate_yaml(struct)

        with open(output, 'w') as f:
            f.write(txt)

    elif target == 'json':
        print("generating json")

        struct = generate_simple_struct(obj_tree)

        txt = generate_json(struct)

        with open(output, 'w') as f:
            f.write(txt)

    elif target == 'c++':
        print(f"generating c++ header file")
        txt = generate_cpp_code(obj_tree)

        with open(output, 'w') as f:
            f.write(txt)

    else:
        raise RuntimeError("invalid target")

    print("exit ok")


if __name__ == '__main__':
    main()
