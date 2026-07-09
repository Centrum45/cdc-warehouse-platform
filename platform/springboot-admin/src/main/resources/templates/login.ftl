<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <title>Login</title>
    <link rel="stylesheet" href="/admin.css">
  </head>
  <body class="login-page">
    <main class="login-main">
      <section class="login-box">
        <h1>CDC Warehouse Admin</h1>
        <form method="post" action="/login">
          <p>
            <label>Username</label>
            <input name="username" autocomplete="username" autofocus>
          </p>
          <p>
            <label>Password</label>
            <input name="password" type="password" autocomplete="current-password">
          </p>
          <#if error??><p class="bad">${error}</p></#if>
          <div class="actions">
            <button type="submit">Login</button>
          </div>
        </form>
      </section>
    </main>
  </body>
</html>
