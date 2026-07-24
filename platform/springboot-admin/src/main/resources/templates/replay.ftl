<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <title>Replay</title>
    <link rel="stylesheet" href="/admin.css">
  </head>
  <body>
    <header>
      <h1>Replay</h1>
      <nav>
        <a href="/">Dashboard</a>
        <a href="/realtime">Realtime</a>
        <a href="/logs">Logs</a>
        <a href="/tasks">Task Config</a>
        <a href="/table-ops">Table Ops</a>
        <a href="/onboarding">Onboarding</a>
        <a href="/replay">Replay</a>
        <a href="/monitors">Monitors</a>
        <a href="/rules">Rules</a>
        <a class="logout" href="/logout">Logout</a>
      </nav>
    </header>
    <main>
      <section>
        <h2>Maxwell Bootstrap Replay</h2>
        <p>Executes a full source MySQL snapshot. Start and end are audit labels only.</p>
        <form method="post" action="/replay">
          <div class="grid">
            <div><label>Database</label><input name="databaseName" value="${request.databaseName}"></div>
            <div><label>Table</label><input name="tableName" value="${request.tableName}"></div>
            <div><label>Start</label><input name="startTime" value="${request.startTime}"></div>
            <div><label>End</label><input name="endTime" value="${request.endTime}"></div>
          </div>
          <div class="actions"><button type="submit">Execute Full Replay</button></div>
        </form>
        <#if error??><pre>${error?html}</pre></#if>
        <#if command??>
        <pre>${command?html}</pre>
        </#if>
        <#if result??>
        <pre>exitCode=${result.exitCode}
${result.output?html}</pre>
        </#if>
      </section>
      <section>
        <h2>Recent Replay Runs</h2>
        <table>
          <thead><tr><th>ID</th><th>Source</th><th>Status</th><th>Created</th><th>Command</th></tr></thead>
          <tbody>
          <#list records as item>
            <tr>
              <td>${item.id}</td>
              <td>${item.databaseName?html}.${item.tableName?html}</td>
              <td>${item.status?html}</td>
              <td>${item.createdAt?html}</td>
              <td><code>${item.command?html}</code></td>
            </tr>
          </#list>
          </tbody>
        </table>
      </section>
    </main>
  </body>
</html>
