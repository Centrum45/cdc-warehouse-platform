<!doctype html>
<html>
  <head><meta charset="utf-8"><title>Rules</title></head>
  <body>
    <h1>Rules</h1>
    <#if message??><p>${message}</p></#if>
    <h2>Sensitive Rule</h2>
    <form method="post" action="/rules/sensitive">
      <p>Column Pattern <input name="columnName" value="${rule.columnName}"></p>
      <p>Action <input name="action" value="${rule.action}"></p>
      <p>Default Value <input name="ruleValue" value="${rule.ruleValue!""}"></p>
      <button type="submit">Save Sensitive Rule</button>
    </form>
    <h2>All Rules</h2>
    <table border="1" cellspacing="0" cellpadding="8">
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
  </body>
</html>
