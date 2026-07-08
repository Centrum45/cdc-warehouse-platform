<!doctype html>
<html>
  <head><meta charset="utf-8"><title>Replay</title></head>
  <body>
    <h1>Replay</h1>
    <form method="post" action="/replay">
      <p>Database <input name="databaseName" value="${request.databaseName}"></p>
      <p>Table <input name="tableName" value="${request.tableName}"></p>
      <p>Start <input name="startTime" value="${request.startTime}"></p>
      <p>End <input name="endTime" value="${request.endTime}"></p>
      <button type="submit">Create Replay</button>
    </form>
    <#if command??>
    <p>${command}</p>
    </#if>
  </body>
</html>
