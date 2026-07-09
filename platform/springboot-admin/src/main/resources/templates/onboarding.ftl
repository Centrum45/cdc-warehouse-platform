<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <title>MySQL To Hive Onboarding</title>
    <link rel="stylesheet" href="/admin.css">
  </head>
  <body>
    <header>
      <h1>MySQL To Hive Onboarding</h1>
      <nav>
        <a href="/">Dashboard</a>
        <a href="/logs">Logs</a>
        <a href="/tasks">Task Config</a>
        <a href="/onboarding">Onboarding</a>
        <a href="/replay">Replay</a>
        <a href="/monitors">Monitors</a>
        <a href="/rules">Rules</a>
      </nav>
    </header>
    <main>
      <section>
        <h2>接入新表</h2>
        <form method="post" action="/onboarding">
          <div class="grid">
            <div><label>Database</label><input name="databaseName" value="${request.databaseName}"></div>
            <div><label>Table</label><input name="tableName" value="${request.tableName}"></div>
            <div><label>DBA Metadata</label><input name="dbaMetadataPath" value="${request.dbaMetadataPath}"></div>
            <div><label>Primary Keys</label><input name="primaryKeys" value="${request.primaryKeys}"></div>
            <div><label>Version Column</label><input name="versionColumn" value="${request.versionColumn}"></div>
            <div><label>Partition Column</label><input name="partitionColumn" value="${request.partitionColumn}"></div>
          </div>
          <div class="actions"><button type="submit">Execute Onboarding</button></div>
        </form>
      </section>
      <section>
        <h2>执行计划</h2>
        <ol>
          <#list plan as item>
          <li>${item}</li>
          </#list>
        </ol>
      </section>
      <#if result??>
      <section>
        <h2>Result</h2>
        <p>Exit Code: <#if result.exitCode == 0><span class="ok">${result.exitCode}</span><#else><span class="bad">${result.exitCode}</span></#if></p>
        <pre>${result.output?html}</pre>
      </section>
      </#if>
    </main>
  </body>
</html>
