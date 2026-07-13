<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <title>Rules</title>
    <link rel="stylesheet" href="/admin.css">
  </head>
  <body>
    <header>
      <h1>Rules</h1>
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
        <h2>Sensitive Rule</h2>
        <#if message??><p class="ok">${message}</p></#if>
        <form method="post" action="/rules/sensitive">
          <div class="grid">
            <div><label>Column Pattern</label><input name="columnName" value="${rule.columnName}"></div>
            <div><label>Action</label><input name="action" value="${rule.action}"></div>
            <div><label>Default Value</label><input name="ruleValue" value="${rule.ruleValue!""}"></div>
          </div>
          <div class="actions"><button type="submit">Save Sensitive Rule</button></div>
        </form>
      </section>
      <section>
        <h2>All Rules</h2>
        <table>
          <tr><th>Category</th><th>Table</th><th>Column</th><th>Type</th><th>Action</th><th>Value</th></tr>
          <#list rules as item>
          <tr>
            <td>${item.ruleCategory!""}</td>
            <td>${item.databaseName!""}.${item.tableName!""}</td>
            <td>${item.columnName!""}</td>
            <td>${item.ruleType!""}</td>
            <td>${item.action!""}</td>
            <td>${item.ruleValue!""}</td>
          </tr>
          </#list>
        </table>
      </section>
    </main>
  </body>
</html>
