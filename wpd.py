import sys
import os.path
import lxml.etree
import getopt
from lxml.builder import E as LBE

import yaml
import json

# from yaml import load, dump
# from yaml import Loader, Dumper

DATA_TYPES = ['int', 'uint', 'fixed', 'object',
              'new_id', 'string', 'array', 'fd', 'enum']


def apply_name_ver_descrs_from_element_to_object(obj, element):

    obj.name = element.get('name', '(no name)')

    descrs = element.xpath('description')
    if len(descrs) != 0:
        descr = descrs[0]
        t = descr.text
        if t is None:
            t = ""
        obj.description = t.strip()
        obj.description_summary = element.get(
            'summary', '(no summary)').strip()


def apply_args_to_object(obj, element):
    args = element.xpath('arg')
    for arg in args:
        arg_o = Argument()
        arg_o.name = arg.get('name', '(no name)')
        arg_o.type_ = arg.get('type', '(no type)')
        arg_o.interface = arg.get('interface', '(no interface)')
        arg_o.summary = arg.get('summary', '(no summary)')

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
    lst.append(['description_summary', obj.description_summary])
    lst.append(['description', obj.description])


class CommonFields:

    def __init__(self):
        self.name = ''
        self.description_summary = ''
        self.description = ''


class ProtocolCollection(CommonFields):

    def __init__(self):
        super().__init__()
        self.protocols = []


class Protocol(CommonFields):

    def __init__(self):
        super().__init__()
        self.basename = ''
        self.dirname = ''
        # self.status = 'unstable'
        self.interfaces = []


class Interface(CommonFields):

    def __init__(self):
        super().__init__()
        self.version = '0'
        self.requests = []
        self.events = []
        self.enums = []


class Message(CommonFields):

    def __init__(self):
        super().__init__()
        self.arguments = []


class Request(Message):
    pass


class Event(Message):
    pass


class Enum(CommonFields):

    def __init__(self):
        super().__init__()
        self.entries = []


class Argument:

    def __init__(self):
        self.name = ''
        self.type_ = ''
        self.interface = ''
        self.summary = ''


class Entry:
    def __init__(self):
        self.name = ''
        self.value = ''
        self.summary = ''


def parse_xml(filename, output_dict):

    filename = os.path.abspath(filename)

    parsed = None

    try:
        with open(filename, 'rb') as f:
            txt = f.read()
            parsed = lxml.etree.fromstring(txt)
    except Exception as e:
        print("can't open, read and parse file. error: {}".format(e))
        print("^^^^ skipping ^^^^: {}".format(filename))
        return

    check_ok = False
    protocol = parsed.xpath('/protocol')
    proto_name = None
    if len(protocol) != 0:
        proto_name = protocol[0].get('name')
        if not proto_name is None:
            check_ok = True

    if check_ok:
        parsed_info = dict()
        # parsed_info['name'] = proto_name
        parsed_info['dirname'] = os.path.relpath(
            os.path.dirname(filename),
            os.path.dirname(
                os.path.abspath(sys.argv[0])
            )
        )
        parsed_info['basename'] = os.path.basename(filename)
        parsed_info['parsed'] = parsed
        
        output_dict[proto_name] = parsed_info


def find_all_xml_files(dirname, output_xml_list):

    dirname = os.path.abspath(dirname)

    dirfiles = os.listdir(dirname)

    for i in dirfiles:

        dirname_i = os.path.join(dirname, i)

        if os.path.isdir(dirname_i) and not os.path.islink(dirname_i):
            find_all_xml_files(dirname_i, output_xml_list)
            continue

        if os.path.isfile(dirname_i) and not os.path.islink(dirname_i):
            if i.endswith('.xml'):
                output_xml_list.append(dirname_i)
            continue


def generate_html_for_parsed(parsed_info, toc, super_toc):

    txt = generate_protocols_html(parsed_info, toc, super_toc)

    return txt


def generate_protocols_html(parsed_info, toc, super_toc):

    ret = lxml.etree.Element('div')

    protocols = parsed_info['parsed'].xpath('/protocol')

    if len(protocols) == 0:
        return ret

    ret.append(
        LBE.div(
            '{} protocol(s) in file: {}'.format(
                len(protocols),
                os.path.basename(parsed_info['basename'])
            )
        )
    )

    protocols_div = lxml.etree.Element('div')

    for protocol in protocols:

        idname_1 = protocol.get('name', '(noname)')
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

        protocol_div = lxml.etree.Element('div', {'id': idname_1})
        protocol_div_name = LBE.div('{}'.format(protocol.get(
            'name', '(noname)')), {'class': 'protocol-name'})
        protocol_div.append(protocol_div_name)

        interfaces = protocol.xpath('interface')

        interfaces_div = lxml.etree.Element('div')
        interfaces_div_txt = LBE.div('{} interface(s)'.format(len(interfaces)))
        interfaces_div.append(interfaces_div_txt)

        for interface in interfaces:

            n = interface.get('name', '(noname)')
            idname_2 = idname_1 + '-'+n

            toc.append(LBE.div({'class': 'level2'}, LBE.a(
                {'href': '#'+idname_2}, 'i: '+n)))

            interface_div = lxml.etree.Element('div', {'id': idname_2})
            interface_div.set('class', 'interface-div')
            interface_div.append(
                LBE.div(
                    'interface: ', LBE.b(interface.get('name', 'unknown'), {
                                         'class': "interface-name"}),
                    ', version: ', LBE.b(interface.get('version', 'unknown')),
                    {"class": "interface-title"}
                )
            )

            descrs = interface.xpath('description')
            if len(descrs) != 0:
                descr = descrs[0]
                interface_div.append(
                    LBE.div(
                        LBE.div(
                            LBE.div('summary: ', descr.get(
                                'summary', '(no summary)')),
                            LBE.div('description: ', getattr(descr, 'text', '(no descr)'), {
                                    'class': 'description-div'})
                        )
                    )
                )

            requests = interface.xpath('request')
            if len(requests) > 0:
                requests_div = LBE.div('', {'class': 'requests-div'})
                for request in requests:

                    n = request.get('name', '(noname)')
                    idname_3 = idname_2 + '-req-' + n

                    toc.append(LBE.div({'class': 'level3'}, LBE.a(
                        {'href': '#'+idname_3}, 'r: '+n)))

                    request_div = LBE.div(
                        "request: ",
                        LBE.b(
                            request.get('name', 'no name'),
                            {'class': 'request-name'}
                        ),
                        {'id': idname_3}
                    )

                    descrs = request.xpath('description')
                    if len(descrs) != 0:
                        descr = descrs[0]
                        t = descr.text
                        if t is None:
                            t = "(do descr)"
                        request_div.append(
                            LBE.div(
                                LBE.div('summary: ', descr.get(
                                    'summary', '(no summary)')),
                                # getattr(descr, 'text', '(no descr)')) #)
                                LBE.div('description: ', t, {
                                    'class': 'description-div'})
                            )
                        )

                    args = request.xpath('arg')
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
                                LBE.td(LBE.b(arg.get('name', '(no name)'),
                                       {'class': 'arg-name'})),
                                LBE.td(arg.get('type', '(no)')),
                                LBE.td(arg.get('interface', '(no)')),
                                LBE.td(arg.get('summary', '(no)')),
                            )
                            args_table.append(arg_row)

                        request_div.append(args_table)
                    requests_div.append(request_div)
                interface_div.append(requests_div)

            events = interface.xpath('event')
            if len(events) > 0:
                events_div = LBE.div('', {'class': 'events-div'})
                for event in events:

                    n = event.get('name', '(noname)')
                    idname_3 = idname_2 + '-ev-' + n

                    toc.append(LBE.div({'class': 'level3'}, LBE.a(
                        {'href': '#'+idname_3}, 'ev: '+n)))

                    event_div = LBE.div(
                        "event: ",
                        LBE.b(
                            event.get('name', 'no name'),
                            {'class': 'event-name'}
                        ),
                        {'id': idname_3}
                    )

                    descrs = event.xpath('description')
                    if len(descrs) != 0:
                        descr = descrs[0]
                        t = descr.text
                        if t is None:
                            t = "(do descr)"
                        event_div.append(
                            LBE.div(
                                LBE.div('summary: ', descr.get(
                                    'summary', '(no summary)')),
                                # getattr(descr, 'text', '(no descr)')) #)
                                LBE.div('description: ', t, {
                                    'class': 'description-div'})
                            )
                        )

                    args = event.xpath('arg')
                    if len(args) > 0:
                        args_table = LBE.table(
                            LBE.tr(
                                LBE.th('arg name'),
                                LBE.th('type'),
                                LBE.th('summary'),
                            ),
                            {'class': 'args-table'}
                        )
                        for arg in args:
                            arg_row = LBE.tr(
                                LBE.td(LBE.b(arg.get('name', '(no name)'),
                                       {'class': 'arg-name'})),
                                LBE.td(arg.get('type', '(no)')),
                                LBE.td(arg.get('summary', '(no)')),

                            )
                            args_table.append(arg_row)

                        event_div.append(args_table)
                    events_div.append(event_div)
                interface_div.append(events_div)

            enums = interface.xpath('enum')
            if len(enums) > 0:
                enums_div = LBE.div('', {'class': 'enums-div'})
                for enum in enums:

                    n = enum.get('name', '(noname)')
                    idname_3 = idname_2 + '-en-' + n

                    toc.append(LBE.div({'class': 'level3'}, LBE.a(
                        {'href': '#'+idname_3}, 'en: '+n)))

                    enum_div = LBE.div(
                        "enum: ",
                        LBE.b(
                            enum.get('name', 'no name'),
                            {'class': 'enum-name'}
                        ),
                        {'id': idname_3}
                    )

                    descrs = enum.xpath('description')
                    if len(descrs) != 0:
                        descr = descrs[0]
                        t = descr.text
                        if t is None:
                            t = "(do descr)"
                        enum_div.append(
                            LBE.div(
                                LBE.div('summary: ', descr.get(
                                    'summary', '(no summary)')),
                                # getattr(descr, 'text', '(no descr)')) #)
                                LBE.div('description: ', t, {
                                    'class': 'description-div'})
                            )
                        )

                    args = enum.xpath('entry')
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
                                LBE.td(LBE.b(arg.get('name', '(no name)'),
                                       {'class': 'arg-name'})),
                                LBE.td(arg.get('value', '(no)')),
                                LBE.td(arg.get('summary', '(no)')),

                            )
                            args_table.append(arg_row)

                        enum_div.append(args_table)
                    enums_div.append(enum_div)
                interface_div.append(enums_div)

            interfaces_div.append(interface_div)

        protocol_div.append(interfaces_div)
        protocols_div.append(protocol_div)

    ret.append(protocols_div)

    return ret


def generate_ProtocolCollection(parsed_docs):

    # stable, staging, unstable = stable_unstable_sort(parsed_docs)

    sorted_proto_name_list = gen_sorted_proto_name_list(parsed_docs)

    ret = ProtocolCollection()

    for i in sorted_proto_name_list:
        protos = generate_protocols_struct_list_for_parsed(parsed_docs[i])
        for proto in protos:
            ret.protocols.append(proto)

    return ret


def generate_protocols_struct_list_for_parsed(parsed_info):

    ret = []

    protocols = parsed_info['parsed'].xpath('/protocol')

    if len(protocols) == 0:
        return None

    for protocol in protocols:

        prot_o = Protocol()

        apply_name_ver_descrs_from_element_to_object(prot_o, protocol)

        prot_o.basename=parsed_info['basename']
        prot_o.dirname=parsed_info['dirname']
        # prot_o.status=parsed_info['status']

        interfaces = protocol.xpath('interface')

        for interface in interfaces:

            interf_o = Interface()

            apply_name_ver_descrs_from_element_to_object(interf_o, interface)

            interf_o.version = interface.get('version', '0')

            interf_o.requests = []
            interf_o.events = []
            interf_o.enums = []

            requests = interface.xpath('request')
            for request in requests:
                request_o = Request()
                apply_name_ver_descrs_from_element_to_object(
                    request_o, request)
                apply_args_to_object(request_o, request)
                interf_o.requests.append(request_o)

            events = interface.xpath('event')
            for event in events:
                event_o = Event()
                apply_name_ver_descrs_from_element_to_object(event_o, event)
                apply_args_to_object(event_o, event)
                interf_o.events.append(event_o)

            enums = interface.xpath('enum')
            for enum in enums:
                enum_o = Enum()

                apply_name_ver_descrs_from_element_to_object(enum_o, enum)

                entrys = enum.xpath('entry')
                for entry in entrys:
                    entry_o = Entry()
                    entry_o.name = entry.get('name', '(no name)')
                    entry_o.value = entry.get('value', '(no value)')
                    entry_o.summary = entry.get('summary', '(no summary)')

                    enum_o.entries.append(entry_o)

                interf_o.enums.append(enum_o)

            prot_o.interfaces.append(interf_o)

        ret.append(prot_o)

    return ret


def generate_simple_struct(list_of_Protocols):

    # note: here are intentionally used list of tuples and not OrderedDict.
    #       order is important in wayland's requests, events and arguments

    proto_od = []

    for protocol in list_of_Protocols.protocols:

        proto_tuple_list = []

        common_fields_from_obj_to_simple_struct(proto_tuple_list, protocol)

        proto_tuple_list.append(['basename', protocol.basename])
        proto_tuple_list.append(['dirname', protocol.dirname])
        #proto_tuple_list.append(['status', protocol.status])

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
                common_fields_from_obj_to_simple_struct(eve_tuple_list, event)

                eve_tuple_list.append(
                    ['args', arguments_simple_struct(event)])

                eves_tuple_list.append(eve_tuple_list)

            # work with enums

            enus_tuple_list = []
            interf_tuple_list.append(['enums', enus_tuple_list])

            for enum in interface.enums:

                enu_tuple_list = []
                common_fields_from_obj_to_simple_struct(enu_tuple_list, enum)

                enu_tuple_list.append(
                    ['entries', entries_simple_struct(enum)])

                enus_tuple_list.append(enu_tuple_list)

            # end of works

            interfs_tuple_list.append(interf_tuple_list)

        proto_od.append(proto_tuple_list)

    return proto_od


def generate_yaml(simple_struct):
    ret = yaml.dump(simple_struct, Dumper=yaml.Dumper)
    return ret


def generate_json(simple_struct):
    ret = json.dumps(simple_struct, indent=4)
    return ret


def generate_html(parsed_docs):

    stable, staging, unstable = stable_unstable_sort(parsed_docs)

    texts = ''

    body = lxml.etree.Element('body')
    main_div = LBE.div('', {'id': 'main-div'})
    toc = LBE.div('', {'id': 'toc-div'})
    super_toc = LBE.div('', {'id': 'supertoc-div'})
    body.append(super_toc)
    body.append(toc)
    body.append(main_div)

    for i in stable:
        x = generate_html_for_parsed(parsed_docs[i], 'stable', toc, super_toc)
        main_div.append(x)

    for i in staging:
        x = generate_html_for_parsed(parsed_docs[i], 'staging', toc, super_toc)
        main_div.append(x)

    for i in unstable:
        x = generate_html_for_parsed(
            parsed_docs[i], 'unstable', toc, super_toc)
        main_div.append(x)

    html_struct = LBE.html(
        LBE.head(
            LBE.title("Wayland Protocols Documentation"),
            LBE.style('''
            body { font-size: 10px; font-family: "Go Mono"; margin: 0; padding: 0;}
            #main-div {margin-left: 210px; margin-right: 210px;}
            #main-div table { font-size: 10px; font-family: "Go Mono"; }
            #main-div div { margin-left: 10px; }
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
            .protocol-name { font-size: 20px; border: 3px solid black; border-radius: 5px; padding: 5px; }
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

    ret = lxml.etree.tostring(html_struct)

    return ret


def calc_doc_stability(name, parsed_info):
    known_stable = ['wayland']

    if name in known_stable:
        return 'stable'

    return 'unstable'


def gen_sorted_proto_name_list(parsed_docs):
    order_list = ['wayland']

    ret = []

    for i in order_list:
        ret.append(i)

    names = list(parsed_docs.keys())
    names.sort()
        
    for i in names:
        if not i in order_list:
            ret.append(i)
        
    return ret

def stable_unstable_sort(parsed_docs):
    order_list = ['wayland']

    stable = []
    staging = []
    unstable = []

    stable_no = []
    staging_no = []
    unstable_no = []

    for i in order_list:
        stabilitiy = calc_doc_stability(i, parsed_docs[i])
        if stabilitiy == 'stable':
            stable.append(i)
            continue
        if stabilitiy == 'staging':
            staging.append(i)
            continue
        if stabilitiy == 'unstable':
            unstable.append(i)
            continue

    for i in parsed_docs:
        if not i in order_list:

            stabilitiy = calc_doc_stability(i, parsed_docs[i])
            if stabilitiy == 'stable':
                stable_no.append(i)
                continue
            if stabilitiy == 'staging':
                staging_no.append(i)
                continue
            if stabilitiy == 'unstable':
                unstable_no.append(i)
                continue

    stable_no.sort()
    staging_no.sort()
    unstable_no.sort()

    stable += stable_no
    staging += staging_no
    unstable += unstable_no

    return stable, staging, unstable


def print_help():
    print(
        """
{cmd} [options] target

  recurcively searches for .xml files in current directory and trying to
  find wayland protocols in them.

  -o  filename    - where to store. of omitted - generated automatically

  valid targets:

     html      - (default) generates index.html with /readabale/ documentation

     yaml      - generates yaml document with yaml representation
                 of all found .xml protocols

     json      - same as yaml, but generates json

     c or c++  - generates C/C++ compatible .h (or .hpp) include file
                 to be included in waylandcc project
                 (see https://github.com/AnimusPEXUS/waylandcc).
                 (generated file' contents is identical, just
                  extension in filename is different)
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

    acceptable_targets = ['html', 'yaml', 'json']

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
        else:
            raise RuntimeError("invalid target")

    print(f"target is {target}. output file is {output}")

    if len(args) != 1:
        raise RuntimeError("invalid arg count")

    cwd = os.path.dirname(os.path.abspath(argv[0]))

    xml_files = []
    find_all_xml_files(cwd, xml_files)

    print("parsing xml")
    parsed_docs = dict()
    for i in xml_files:
        parse_xml(i, parsed_docs)

    if target == 'html':

        txt = generate_html(parsed_docs)

        with open(output, 'wb') as f:
            f.write(txt)

        return

    elif target == 'yaml':

        obj_tree = generate_ProtocolCollection(parsed_docs)

        struct = generate_simple_struct(obj_tree)

        txt = generate_yaml(struct)

        with open(output, 'w') as f:
            f.write(txt)

        return

    elif target == 'json':

        obj_tree = generate_ProtocolCollection(parsed_docs)

        struct = generate_simple_struct(obj_tree)

        txt = generate_json(struct)

        with open(output, 'w') as f:
            f.write(txt)

        return


if __name__ == '__main__':
    main()
