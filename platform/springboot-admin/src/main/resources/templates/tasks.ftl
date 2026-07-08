<!doctype html>
<html>
  <head><meta charset="utf-8"><title>Task Config</title></head>
  <body>
    <h1>Task Config</h1>
    <#if message??><p>${message}</p></#if>
    <form method="post" action="/tasks">
      <p>Name <input name="taskName" value="${task.taskName}"></p>
      <p>Type <input name="taskType" value="${task.taskType}"></p>
      <p>Command <input name="command" value="${task.command}" size="96"></p>
      <p>Schedule <input name="schedule" value="${task.schedule}"></p>
      <button type="submit">Save Task</button>
    </form>
    <table border="1" cellspacing="0" cellpadding="8">
      <tr><th>Name</th><th>Type</th><th>Command</th><th>Schedule</th></tr>
      <#list tasks as task>
      <tr>
        <td>${task.taskName}</td>
        <td>${task.taskType}</td>
        <td>${task.command}</td>
        <td>${task.schedule}</td>
      </tr>
      </#list>
    </table>
  </body>
</html>
