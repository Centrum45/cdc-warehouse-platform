<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <title>Logs</title>
    <link rel="stylesheet" href="/admin.css">
  </head>
  <body>
    <header>
      <h1>Logs</h1>
      <div class="refresh">Auto refresh: 5s <small id="refreshStatus"></small></div>
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
        <h2>日志控制</h2>
        <div class="actions">
          <button type="button" onclick="refreshLogs()">Refresh</button>
          <button type="button" class="secondary" onclick="toggleWrap()">Wrap</button>
          <span class="muted">Last refresh: <span id="refreshedAt">${dashboard.refreshedAt?html}</span></span>
        </div>
      </section>

      <section class="log-panel">
        <h2>Maxwell</h2>
        <pre id="maxwellLogs" class="log-output" data-follow="true">${dashboard.maxwellLogs?html}</pre>
      </section>

      <section class="log-panel">
        <h2>Kafka</h2>
        <pre id="kafkaLogs" class="log-output" data-follow="true">${dashboard.kafkaLogs?html}</pre>
      </section>

      <section class="log-panel">
        <h2>Kafka Topics</h2>
        <pre id="kafkaTopics" class="log-output" data-follow="true">${dashboard.kafkaTopics?html}</pre>
      </section>

      <section class="log-panel">
        <h2>SparkStreaming</h2>
        <pre id="sparkStreamingLogs" class="log-output" data-follow="true">${dashboard.sparkStreamingLogs?html}</pre>
      </section>

      <section class="log-panel">
        <h2>SparkSQL Merge</h2>
        <pre id="sparkSqlMergeLogs" class="log-output" data-follow="true">${dashboard.sparkSqlMergeLogs?html}</pre>
      </section>

      <section class="log-panel">
        <h2>Admin</h2>
        <pre id="adminLogs" class="log-output" data-follow="true">${dashboard.adminLogs?html}</pre>
      </section>

      <section class="log-panel">
        <h2>HDFS NameNode</h2>
        <pre id="hdfsNamenodeLogs" class="log-output" data-follow="true">${dashboard.hdfsNamenodeLogs?html}</pre>
      </section>

      <section class="log-panel">
        <h2>容器状态</h2>
        <pre id="containerStatus" class="log-output" data-follow="true">${dashboard.containerStatus?html}</pre>
      </section>
    </main>
    <script>
      var wrapEnabled = true;

      function nearBottom(el) {
        return el.scrollHeight - el.scrollTop - el.clientHeight < 24;
      }

      function setText(id, value) {
        var el = document.getElementById(id);
        if (!el) return;
        var previousTop = el.scrollTop;
        var follow = el.dataset.follow === "true" && nearBottom(el);
        el.textContent = value || "";
        if (follow) {
          el.scrollTop = el.scrollHeight;
        } else {
          el.scrollTop = previousTop;
        }
      }

      function toggleWrap() {
        wrapEnabled = !wrapEnabled;
        document.querySelectorAll(".log-output").forEach(function (el) {
          el.classList.toggle("no-wrap", !wrapEnabled);
        });
      }

      function refreshLogs() {
        fetch("/api/dashboard", { cache: "no-store" })
          .then(function (response) { return response.json(); })
          .then(function (data) {
            document.getElementById("refreshedAt").textContent = data.refreshedAt || "";
            setText("maxwellLogs", data.maxwellLogs);
            setText("kafkaLogs", data.kafkaLogs);
            setText("kafkaTopics", data.kafkaTopics);
            setText("sparkStreamingLogs", data.sparkStreamingLogs);
            setText("sparkSqlMergeLogs", data.sparkSqlMergeLogs);
            setText("adminLogs", data.adminLogs);
            setText("hdfsNamenodeLogs", data.hdfsNamenodeLogs);
            setText("containerStatus", data.containerStatus);
            document.getElementById("refreshStatus").textContent = "updated";
          })
          .catch(function () {
            document.getElementById("refreshStatus").textContent = "refresh failed";
          });
      }

      document.querySelectorAll("pre[data-follow='true']").forEach(function (el) {
        el.scrollTop = el.scrollHeight;
      });
      setInterval(refreshLogs, 5000);
    </script>
  </body>
</html>
