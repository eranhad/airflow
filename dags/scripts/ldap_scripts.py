import ldap
from ldap.controls import SimplePagedResultsControl

def query_ldap(searchFilter="(samAccountName=some_default_user)", searchAttribute=["cn"]):
    connect = ldap.initialize('ldap://ldap_server_name:3268')
    connect.set_option(ldap.OPT_REFERRALS, 0)
    connect.simple_bind_s('user_name', 'password')
    page_control = SimplePagedResultsControl(True, size=1000, cookie='')

    response = connect.search_ext('DC=company_name,DC=com',
                               ldap.SCOPE_SUBTREE,
                               searchFilter, searchAttribute,
                               serverctrls=[page_control])
    result = []
    pages = 0

    while True:
        pages += 1
        rtype, rdata, rmsgid, serverctrls = connect.result3(response)
        result.extend(rdata)
        controls = [control for control in serverctrls if control.controlType == SimplePagedResultsControl.controlType]
    
        if not controls:
            print('The server ignores RFC 2696 control')
            break
    
        if not controls[0].cookie:
            break
    
        page_control.cookie = controls[0].cookie
        response = connect.search_ext('DC=company_name,DC=com',
                               ldap.SCOPE_SUBTREE,
                               searchFilter, searchAttribute,
                               serverctrls=[page_control])

    return result
