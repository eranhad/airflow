# Query LDAP using pagination

This DAG querys LDAP using a function from scripts dir (for reuse) in pagination so I can get all results over our LDAP limit of 1000.
There are two variables to configure:

* `searchFilter="(UserAccountControl=514)"` The filter to use for ldap search. In my case it is disabled users (514)
* `searchAttribute = ["sAMAccountName", "mail","distinguishedName", "Description", "manager", "title", "department", "displayName"]` List of attributes to get back from LDAP
        
