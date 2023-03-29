# Databricks notebook source
#get the file name from adf
#fileName=dbutils.widgets.get('fileName')
fileName='Product.csv'
fileNameWithoutExt=fileName.split('.')[0]
print(fileNameWithoutExt)

# COMMAND ----------

import pyspark.sql.functions as F

sqlDbName = 'atmadatabase'
dbUserName = 'atma7205'
passwordKey = 'sqlpasswordkey'
stgAccountSASTokenKey = 'sastokenforstorage'
landingFileName =fileName #'Product'  #dbutils.widgets.get('Product')
databricksScopeName ='project2scope'
dbServer = 'atmasqlserver'
dbServerPortNumber ='1433'
storageContainer ='inputdata'
storageAccount='storageatma'
landingMountPoint ='/mnt'

# COMMAND ----------

#mounting storage in databricks
#check if mount point exist
if not any (mount.mountPoint==landingMountPoint for mount in dbutils.fs.mounts()):
    dbutils.fs.mount(source = 'wasbs://{}@{}.blob.core.windows.net'.format(storageContainer,storageAccount),mount_point=landingMountPoint,extra_configs={'fs.azure.sas.{}.{}.blob.core.windows.net'.format(storageContainer,storageAccount):dbutils.secrets.get(scope = databricksScopeName, key= stgAccountSASTokenKey)})
    print('Mounted the storage account successfully')
    
else:
    print('Storage account already mounted')


# COMMAND ----------

#connect to Azure SQL DB
dbPassword = dbutils.secrets.get(scope = databricksScopeName, key= passwordKey)
serverurl = 'jdbc:sqlserver://{}.database.windows.net:{};database={};user={};'.format(dbServer, dbServerPortNumber,sqlDbName,dbUserName)
connectionProperties = {
    'password':dbPassword,
    'driver':'com.microsoft.sqlserver.jdbc.SQLServerDriver'
}
df = spark.read.jdbc(url = serverurl, table = 'dbo.FileDetailsFormat', properties= connectionProperties)
display(df)


# COMMAND ----------

df1=spark.read.csv('/mnt/landing/'+fileName,inferSchema=True,header=True)

#rule1
errorFlag=False
errorMessage=''
totalcount=df1.count()
print(totalcount)
distinctCount=df1.distinct().count()
print(distinctCount)
if distinctCount != totalcount:
    errorFlag=True
    errorMessage='Duplication Found. Rule 1 Failed'
print(errorMessage)

#rule 2

df2=df.filter(df.FileName==fileNameWithoutExt).select('ColumnName','ColumnDateFormat')
display(df2)
rows=df2.collect()
print(rows)
for r in rows:
    colName=r[0]
    colFormat=r[1]
    print(colName,colFormat)
    formatCount=df1.filter(F.to_date(colName,colFormat).isNotNull()==True).count()
    if formatCount==totalcount:
        errorFlag=True
        errorMessage=errorMessage+' DateFormate is incorrect for {} '.format(colName)
        
    else:
        print('All rows are good for {}'.format(colName))
print(errorMessage)
if errorFlag:
    dbutils.fs.cp('/mnt/landing/'+fileName,'/mnt/rejected/'+fileName )
    dbutils.notebook.exit('{"errorFlag": "true", "errorMessage":'+errorMessage+'}')
else:
    dbutils.fs.cp('/mnt/landing/'+fileName,'/mnt/staging/'+fileName )
    dbutils.notebook.exit('{"errorFlag": "false", "errorMessage":"No error"}')


# COMMAND ----------


