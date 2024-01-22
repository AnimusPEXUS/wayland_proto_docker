import sys
import os.path
import lxml.etree
from lxml.builder import E as LBE


def parse_xml(filename, output_dict):

    filename = os.path.abspath(filename)

    parsed = None

    try:
        with open(filename, 'rb') as f:
            txt = f.read()
            parsed = lxml.etree.fromstring(txt)
    except Exception as e:
        print("can't open, read and parse file. error: {}".format(e))
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
        parsed_info['dirname'] = os.path.dirname(filename)
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


def generate_html_for_parsed(parsed_info, stable_status, toc, super_toc):

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
                    'id':super_idname_1
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
        x = generate_html_for_parsed(parsed_docs[i], 'unstable', toc, super_toc)
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


def main():

    argv = sys.argv
    len_argv = len(argv)

    if len_argv == 0:
        raise RuntimeError("invalid sys.argv")

    if argv[0] == '-c':
        raise RuntimeError("this must be run as script")

    cwd = os.path.dirname(os.path.abspath(argv[0]))

    xml_files = []
    find_all_xml_files(cwd, xml_files)

    parsed_docs = dict()
    for i in xml_files:
        parse_xml(i, parsed_docs)

    txt = generate_html(parsed_docs)

    with open('index.html', 'wb') as f:
        f.write(txt)


if __name__ == '__main__':
    main()
