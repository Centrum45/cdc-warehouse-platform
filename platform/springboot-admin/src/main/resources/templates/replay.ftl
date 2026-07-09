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
        <a href="/logs">Logs</a>
        <a href="/tasks">Task Config</a>
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
        <form method="post" action="/replay">
          <div class="grid">
            <div><label>Database</label><input name="databaseName" value="${request.databaseName}"></div>
            <div><label>Table</label><input name="tableName" value="${request.tableName}"></div>
            <div><label>Start</label><input name="startTime" value="${request.startTime}"></div>
            <div><label>End</label><input name="endTime" value="${request.endTime}"></div>
          </div>
          <div class="actions"><button type="submit">Create Replay</button></div>
        </form>
        <#if command??>
        <pre>${command?html}</pre>
        </#if>
      </section>
    </main>
  </body>
</html>
