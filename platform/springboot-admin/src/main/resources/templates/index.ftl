<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <title>CDC Warehouse Admin</title>
    <style>
      body { margin: 0; font-family: Arial, sans-serif; background: #f6f7f9; color: #1f2933; }
      header { background: #263238; color: white; padding: 18px 28px; }
      header h1 { margin: 0; font-size: 22px; }
      nav { margin-top: 10px; }
      nav a { color: #dbeafe; margin-right: 18px; text-decoration: none; font-size: 14px; }
      main { padding: 22px 28px 40px; }
      section { background: white; border: 1px solid #d9dee5; border-radius: 6px; margin-bottom: 18px; padding: 18px; }
      h2 { margin: 0 0 14px; font-size: 18px; }
      h3 { margin: 16px 0 10px; font-size: 15px; }
      table { width: 100%; border-collapse: collapse; font-size: 13px; }
      th, td { border: 1px solid #e1e5ea; padding: 8px; text-align: left; vertical-align: top; }
      th { background: #f0f3f7; }
      label { display: block; font-size: 12px; font-weight: bold; margin-bottom: 5px; color: #52606d; }
      input { width: 100%; box-sizing: border-box; padding: 8px; border: 1px solid #cbd2d9; border-radius: 4px; }
      button { background: #0f766e; color: white; border: 0; border-radius: 4px; padding: 9px 14px; cursor: pointer; }
      pre { background: #111827; color: #e5e7eb; padding: 12px; border-radius: 4px; overflow: auto; max-height: 320px; font-size: 12px; line-height: 1.45; }
      .grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
      .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
      .muted { color: #657383; font-size: 13px; }
      .ok { color: #047857; font-weight: bold; }
      .bad { color: #b91c1c; font-weight: bold; }
      .path { font-family: Menlo, monospace; font-size: 12px; color: #334155; }
      .actions { margin-top: 14px; display: flex; gap: 10px; align-items: center; }
      .refresh { float: right; color: #cbd5e1; font-size: 13px; margin-top: 4px; }
      .refresh small { color: #94a3b8; }
      @media (max-width: 900px) {
        .grid, .grid-2 { grid-template-columns: 1fr; }
      }
    </style>
  </head>
  <body>
    <header>
      <h1>CDC Warehouse Admin</h1>
      <div class="refresh">Auto refresh: 5s <small id="refreshStatus"></small></div>
      <nav>
        <a href="/">Dashboard</a>
        <a href="/tasks">Task Config</a>
        <a href="/onboarding">Onboarding</a>
        <a href="/replay">Replay</a>
        <a href="/monitors">Monitors</a>
        <a href="/rules">Rules</a>
      </nav>
    </header>
    <main>
      <section>
        <h2>接入新 MySQL 表</h2>
        <form method="post" action="/">
          <div class="grid">
            <div>
              <label>Database</label>
              <input name="databaseName" value="${request.databaseName}">
            </div>
            <div>
              <label>Table</label>
              <input name="tableName" value="${request.tableName}">
            </div>
            <div>
              <label>DBA Metadata Path</label>
              <input name="dbaMetadataPath" value="${request.dbaMetadataPath}">
            </div>
            <div>
              <label>Primary Keys</label>
              <input name="primaryKeys" value="${request.primaryKeys}">
            </div>
            <div>
              <label>Version Column</label>
              <input name="versionColumn" value="${request.versionColumn}">
            </div>
            <div>
              <label>Partition Column</label>
              <input name="partitionColumn" value="${request.partitionColumn}">
            </div>
          </div>
          <div class="actions">
            <button type="submit">生成元数据并全量同步</button>
            <span class="muted">执行后写 metadata / DDL / merge SQL，并用 MySQL 当前全表重建 ODS 初始快照。</span>
          </div>
        </form>
        <h3>执行计划</h3>
        <ol>
          <#list plan as item>
          <li>${item}</li>
          </#list>
        </ol>
        <#if result??>
        <h3>接入结果</h3>
        <p>Exit Code: <#if result.exitCode == 0><span class="ok">${result.exitCode}</span><#else><span class="bad">${result.exitCode}</span></#if></p>
        <pre>${result.output?html}</pre>
        </#if>
      </section>

      <section>
        <h2>已接入表</h2>
        <table>
          <tr>
            <th>Database</th>
            <th>Table</th>
            <th>ODS Binlog</th>
            <th>ODS Snapshot</th>
            <th>Primary Keys</th>
            <th>Version</th>
            <th>Partition</th>
          </tr>
          <#list tables as table>
          <tr>
            <td>${table.databaseName}</td>
            <td>${table.tableName}</td>
            <td>${table.odsBinlogTable}</td>
            <td>${table.odsTable}</td>
            <td>${table.primaryKeys?join(",")}</td>
            <td>${table.versionColumn}</td>
            <td>${table.partitionColumn}</td>
          </tr>
          </#list>
        </table>
      </section>

      <section>
        <h2>ODS / ODS Binlog 数据</h2>
        <#list dashboard.tableStorage as storage>
        <h3>${storage.databaseName}.${storage.tableName}</h3>
        <div class="grid-2">
          <div>
            <div class="path">${storage.odsBinlogPath}</div>
            <pre>${storage.odsBinlogSample?html}</pre>
          </div>
          <div>
            <div class="path">${storage.odsPath}</div>
            <pre>${storage.odsSample?html}</pre>
          </div>
        </div>
        </#list>
      </section>

      <section>
        <h2>Kafka 信息</h2>
        <p class="muted">Last refresh: <span id="refreshedAt">${dashboard.refreshedAt?html}</span> · Snapshot refresher: <span class="path">docker compose -f docker/docker-compose.yml up -d ops-refresh</span></p>
        <div class="grid-2">
          <div>
            <h3>Topics</h3>
            <pre id="kafkaTopics" data-follow="true">${dashboard.kafkaTopics?html}</pre>
          </div>
          <div>
            <h3>Kafka Logs</h3>
            <pre id="kafkaLogs" data-follow="true">${dashboard.kafkaLogs?html}</pre>
          </div>
        </div>
      </section>

      <section>
        <h2>Maxwell 日志</h2>
        <pre id="maxwellLogs" data-follow="true">${dashboard.maxwellLogs?html}</pre>
      </section>

      <section>
        <h2>SparkStreaming 日志</h2>
        <pre id="sparkStreamingLogs" data-follow="true">${dashboard.sparkStreamingLogs?html}</pre>
      </section>

      <section>
        <h2>SparkSQL Merge 日志</h2>
        <pre id="sparkSqlMergeLogs" data-follow="true">${dashboard.sparkSqlMergeLogs?html}</pre>
      </section>

      <section>
        <h2>HDFS / Hive</h2>
        <div class="grid-2">
          <div>
            <h3>HDFS /warehouse</h3>
            <pre id="hdfsWarehouseListing" data-follow="true">${dashboard.hdfsWarehouseListing?html}</pre>
          </div>
          <div>
            <h3>Hive Databases</h3>
            <pre id="hiveDatabases" data-follow="true">${dashboard.hiveDatabases?html}</pre>
          </div>
          <div>
            <h3>NameNode Logs</h3>
            <pre id="hdfsNamenodeLogs" data-follow="true">${dashboard.hdfsNamenodeLogs?html}</pre>
          </div>
          <div>
            <h3>HiveServer2 Logs</h3>
            <pre id="hiveServerLogs" data-follow="true">${dashboard.hiveServerLogs?html}</pre>
          </div>
        </div>
      </section>

      <section>
        <h2>容器状态</h2>
        <pre id="containerStatus" data-follow="true">${dashboard.containerStatus?html}</pre>
      </section>

      <section>
        <h2>Admin 日志</h2>
        <pre id="adminLogs" data-follow="true">${dashboard.adminLogs?html}</pre>
      </section>
    </main>
    <script>
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

      function refreshDashboard() {
        fetch("/api/dashboard", { cache: "no-store" })
          .then(function (response) { return response.json(); })
          .then(function (data) {
            document.getElementById("refreshedAt").textContent = data.refreshedAt || "";
            setText("kafkaTopics", data.kafkaTopics);
            setText("kafkaLogs", data.kafkaLogs);
            setText("maxwellLogs", data.maxwellLogs);
            setText("sparkStreamingLogs", data.sparkStreamingLogs);
            setText("sparkSqlMergeLogs", data.sparkSqlMergeLogs);
            setText("hdfsWarehouseListing", data.hdfsWarehouseListing);
            setText("hdfsNamenodeLogs", data.hdfsNamenodeLogs);
            setText("hiveDatabases", data.hiveDatabases);
            setText("hiveServerLogs", data.hiveServerLogs);
            setText("containerStatus", data.containerStatus);
            setText("adminLogs", data.adminLogs);
            document.getElementById("refreshStatus").textContent = "updated";
          })
          .catch(function () {
            document.getElementById("refreshStatus").textContent = "refresh failed";
          });
      }

      document.querySelectorAll("pre[data-follow='true']").forEach(function (el) {
        el.scrollTop = el.scrollHeight;
      });
      setInterval(refreshDashboard, 5000);
    </script>
  </body>
</html>
