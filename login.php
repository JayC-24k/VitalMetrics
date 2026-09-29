<?php
declare(strict_types=1);
require __DIR__ . '/php/private/bootstrap.php';

$next = safe_next_path($_GET['next'] ?? null);
$error = $_GET['error'] ?? '';
$token = csrf_token();
auth_page_start('Iniciar sesión');
?>
<main class="auth-section"><div class="container"><div class="auth-card">
  <div class="text-center mb-4"><span class="eyebrow">VITALMETRICS</span><h1 class="h2 fw-bold mt-2">Qué bueno verte</h1><p class="text-secondary">Inicia sesión para acceder a tu evaluación.</p></div>
  <?php if ($error === 'invalid'): ?><div class="alert alert-danger">Usuario o contraseña incorrectos.</div><?php elseif ($error === 'csrf'): ?><div class="alert alert-warning">La sesión del formulario venció. Inténtalo de nuevo.</div><?php elseif ($error === 'server'): ?><div class="alert alert-danger">No fue posible conectar con la base de datos.</div><?php endif; ?>
  <form method="post" action="<?= h(app_path('validar_login.php')) ?>">
    <input type="hidden" name="csrf_token" value="<?= h($token) ?>"><input type="hidden" name="next" value="<?= h($next) ?>">
    <div class="mb-3"><label class="form-label" for="username">Usuario</label><input class="form-control form-control-lg" id="username" name="username" autocomplete="username" required autofocus></div>
    <div class="mb-4"><label class="form-label" for="password">Contraseña</label><input class="form-control form-control-lg" id="password" name="password" type="password" autocomplete="current-password" required></div>
    <button class="btn btn-primary btn-lg w-100" type="submit">Iniciar sesión</button>
  </form>
  <p class="text-center mt-4 mb-0">¿Primera vez aquí? <a href="<?= h(app_path('registrar.php')) ?>">Crea una cuenta</a></p>
</div></div></main>
<?php auth_page_end(); ?>
