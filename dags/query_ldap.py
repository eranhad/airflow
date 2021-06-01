from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta
from airflow.utils.dates import days_ago
from airflow.providers.microsoft.mssql.hooks.mssql import MsSqlHook
from scripts.sql_scripts import *
from scripts.ldap_scripts import query_ldap
from datetime import datetime

start_time = datetime.now()

# Default settings we wish to apply to all tasks/operators
default_args = {
    'owner': 'eranh',
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'email_on_failure': True,
    'email_on_retry': True,
    'email': 'username@company.co.il'
}

def insert_sql_ldap(conn, query, dic):
    try:
        sAMAccountName=dic.get("sAMAccountName", None)
        displayName=dic.get("displayName", None)
        distinguishedName=dic.get("distinguishedName", None)
        mail=dic.get("mail", None)
        description=dic.get("description", None)
        manager=dic.get("manager", None)
        title=dic.get("title", None)
        department=dic.get("department", None)
        
        #convert to unicode for hebrew
        if displayName:
            dispName=displayName[0].decode('UTF-8')
        else:
            dispName=None
        if description:
            desc=description[0].decode('UTF-8')
        else:
            desc=None
        if department:
            dept=department[0].decode('UTF-8')
        else:
            dept=None
        if title:
            tit=title[0].decode('UTF-8')
        else:
            tit=None


        cursor = conn.cursor()
        cursor.execute(query, (sAMAccountName, dispName, distinguishedName, mail, desc, manager, tit, dept))

    except Exception as e:
        error = f"error occurred while writing LDAP data to SQL: {e}"
        conn.rollback()
        raise Exception(error)

    else:
        conn.commit()


def get_ldap_disabled_users():
    try:
        searchFilter="(UserAccountControl=514)"
        searchAttribute = ["sAMAccountName", "mail","distinguishedName", "Description", "manager", "title", "department", "displayName"]
        
        result = []
        result = query_ldap(searchFilter, searchAttribute)

        #Connect to MSSQL
        mssql_hook = MsSqlHook(mssql_conn_id='SQL_DBADB')
        conn = mssql_hook.get_conn()
        
        #Truncate destination table first
        cursor = conn.cursor()
        cursor.execute("TRUNCATE TABLE [dbo].ldapDisabledAccounts")

        query = f""" \
INSERT INTO [dbo].ldapDisabledAccounts \
(sAMAccountName, displayName, distinguishedName, mail, description, manager, title, department) \
VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
        
        #run on ldap results only if not empty
        if len(result) > 0:
            for record in result:
                #example of a record
                '''            
                (
                    'CN=eranh,OU=some_ou,DC=company,DC=com', 
                    {
                        'title': [b'DBA'], 'distinguishedName': [b'CN=eranh,OU=some_ou,DC=company,DC=com'], 
                        'displayName': [b'somevlaue'], 
                        'department': [b'somevalue'], 
                        'sAMAccountName': [b'eranh'], 
                        'mail': [b'eranh@harel-ins.co.il'], 
                        'manager': [b'CN=orend,OU=some_ou,DC=company,DC=com']
                    }
                )
                '''
                dic = record[1]
                insert_sql_ldap(conn, query, dic)

    except Exception as e:
        error = f"error occurred while fatching records from LDAP: {e}"
        mssql_hook = MsSqlHook(mssql_conn_id='SQL_DBADB')
        conn = mssql_hook.get_conn()
        write_log_dbadb(conn, "disabledUsers", start_time, datetime.now(), 0, error)
        raise Exception(error)

with DAG('disabledAccounts',  # name must be unique acgross all DAGs
         default_args=default_args,
         start_date=days_ago(1),    # another option for start date
         schedule_interval='@weekly',  # run once a week at midnight on Sunday morning
         catchup=False  # disabling historical dag-runs from running
         ) as dag:

  
    get_ldap_disabled_users = PythonOperator(
        task_id = 'get_ldap_disabled_users',
        python_callable = get_ldap_disabled_users,
        dag = dag
    )

    
get_ldap_disabled_users
