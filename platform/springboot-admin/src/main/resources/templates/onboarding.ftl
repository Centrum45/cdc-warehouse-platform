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
        <div class="actions">
          <button type="button" class="secondary" onclick="verifyOnboardedTable(this)">接入后验收</button>
        </div>
        <pre>${result.output?html}</pre>
        <pre id="onboardingVerifyResult"></pre>
      </section>
      </#if>
    </main>
    <script>
      function verifyOnboardedTable(button) {
        var previous = button.textContent;
        var body = new URLSearchParams();
        body.set("databaseName", document.querySelector("[name='databaseName']").value);
        body.set("tableName", document.querySelector("[name='tableName']").value);
        body.set("bizDt", "");
        body.set("startDt", "");
        body.set("endDt", "");
        body.set("dryRun", "false");
        button.disabled = true;
        button.textContent = "Running";
        document.getElementById("onboardingVerifyResult").textContent = "running onboarding verify ...";
        fetch("/api/table-ops/onboarding-verify", {
          method: "POST",
          headers: { "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8" },
          body: body
        })
          .then(function (response) { return response.json(); })
          .then(function (data) {
            document.getElementById("onboardingVerifyResult").textContent = "exitCode=" + data.exitCode + "\n" + (data.output || "");
          })
          .catch(function (error) {
            document.getElementById("onboardingVerifyResult").textContent = String(error);
          })
          .finally(function () {
            button.disabled = false;
            button.textContent = previous;
          });
      }
    </script>
  </body>
</html>
