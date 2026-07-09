<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <title>Task Config</title>
    <link rel="stylesheet" href="/admin.css">
  </head>
  <body>
    <header>
      <h1>Task Config</h1>
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
        <h2>新增调度任务</h2>
        <#if message??><p class="ok">${message}</p></#if>
        <form method="post" action="/tasks">
          <div class="grid">
            <div><label>Name</label><input name="taskName" value="${task.taskName}"></div>
            <div><label>Type</label><input name="taskType" value="${task.taskType}"></div>
            <div><label>Schedule</label><input name="schedule" value="${task.schedule}"></div>
          </div>
          <p><label>Command</label><input name="command" value="${task.command}"></p>
          <div class="actions"><button type="submit">Save Task</button></div>
        </form>
      </section>
      <section>
        <h2>已配置任务</h2>
        <table>
          <tr><th>Name</th><th>Type</th><th>Command</th><th>Schedule</th><th>Action</th></tr>
          <#list tasks as task>
          <tr>
            <td>${task.taskName}</td>
            <td>${task.taskType}</td>
            <td class="path">${task.command}</td>
            <td>${task.schedule}</td>
            <td><button type="button" onclick="runTask('${task.taskName?js_string}', this)">Run</button></td>
          </tr>
          </#list>
        </table>
        <pre id="taskRunResult"></pre>
      </section>
    </main>
    <script>
      function runTask(taskName, button) {
        var previous = button.textContent;
        var result = document.getElementById("taskRunResult");
        button.disabled = true;
        button.textContent = "Running";
        result.textContent = "running " + taskName + " ...";
        fetch("/api/tasks/run/" + encodeURIComponent(taskName), { method: "POST" })
          .then(function (response) { return response.json(); })
          .then(function (data) {
            result.textContent = "exitCode=" + data.exitCode + "\n" + (data.output || "");
          })
          .catch(function (error) {
            result.textContent = String(error);
          })
          .finally(function () {
            button.disabled = false;
            button.textContent = previous;
          });
      }
    </script>
  </body>
</html>
