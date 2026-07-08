<!doctype html>
<html>
  <head><meta charset="utf-8"><title>Monitors</title></head>
  <body>
    <h1>Monitors</h1>
    <ul>
      <#list items as item>
      <li>${item}</li>
      </#list>
    </ul>
    <h2>Latest Results</h2>
    <table border="1" cellspacing="0" cellpadding="8">
      <tr>
        <th>Type</th>
        <th>Table</th>
        <th>Status</th>
        <th>Message</th>
        <th>Metric</th>
        <th>Created At</th>
      </tr>
      <#list results as result>
      <tr>
        <td>${result.monitorType}</td>
        <td>${result.databaseName}.${result.tableName}</td>
        <td>${result.status}</td>
        <td>${result.message!""}</td>
        <td>${result.metricValue!""}</td>
        <td>${result.createdAt}</td>
      </tr>
      </#list>
    </table>
  </body>
</html>
