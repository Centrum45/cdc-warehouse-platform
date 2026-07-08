<!doctype html>
<html>
  <head><meta charset="utf-8"><title>MySQL To Hive Onboarding</title></head>
  <body>
    <h1>MySQL To Hive Onboarding</h1>
    <form method="post" action="/onboarding">
      <p>Database <input name="databaseName" value="${request.databaseName}"></p>
      <p>Table <input name="tableName" value="${request.tableName}"></p>
      <p>DBA Metadata <input name="dbaMetadataPath" value="${request.dbaMetadataPath}" size="72"></p>
      <p>Primary Keys <input name="primaryKeys" value="${request.primaryKeys}"></p>
      <p>Version Column <input name="versionColumn" value="${request.versionColumn}"></p>
      <p>Partition Column <input name="partitionColumn" value="${request.partitionColumn}"></p>
      <button type="submit">Execute Onboarding</button>
    </form>
    <ol>
      <#list plan as item>
      <li>${item}</li>
      </#list>
    </ol>
    <#if result??>
    <h2>Result</h2>
    <p>Exit Code: ${result.exitCode}</p>
    <pre>${result.output}</pre>
    </#if>
  </body>
</html>
