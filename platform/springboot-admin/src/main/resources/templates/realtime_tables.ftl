<table>
  <tr>
    <th>Table</th>
    <th>Rows</th>
    <th>Latest Update</th>
  </tr>
  <#list snapshot.tables as table>
  <tr>
    <td>${table.name?html}</td>
    <td>${table.rowCount}</td>
    <td>${table.latestUpdateTime!""}</td>
  </tr>
  </#list>
  <#if snapshot.tables?size == 0>
  <tr><td colspan="3" class="muted">no realtime tables</td></tr>
  </#if>
</table>
