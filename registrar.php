<?php
declare(strict_types=1);
require __DIR__ . '/php/private/bootstrap.php';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $next = safe_next_path($_POST['next'] ?? null);
    if (!valid_csrf_token()) {
        redirect_auth_error('registrar.php', 'csrf', $next);
    }

    $username = trim((string) ($_POST['username'] ?? ''));
    $email = trim((string) ($_POST['email'] ?? ''));
    $password = (string) ($_POST['password'] ?? '');
    if ($username === '' || strlen($username) > 191 || strlen($password) < 8
        || ($email !== '' && (!filter_var($email, FILTER_VALIDATE_EMAIL) || strlen($email) > 255))) {
        redirect_auth_error('registrar.php', 'invalid', $next);
    }

    try {
        $pdo = db();
        $statement = $pdo->prepare(
            "INSERT INTO users (username, email, password, role, created_at)
             VALUES (?, ?, ?, 'user', CURRENT_TIMESTAMP)"
        );
        $statement->execute([$username, $email !== '' ? $email : null, password_hash_compatible($password)]);
        render_session_bridge(issue_login_ticket((int) $pdo->lastInsertId(), $next));
    } catch (PDOException $error) {
        if ($error->getCode() === '23000') {
            redirect_auth_error('registrar.php', 'exists', $next);
        }
        error_log('VitalMetrics PHP registration failed: ' . $error->getMessage());
        redirect_auth_error('registrar.php', 'server', $next);
    } catch (RuntimeException $error) {
        error_log('VitalMetrics PHP registration failed: ' . $error->getMessage());
        redirect_auth_error('registrar.php', 'server', $next);
    }
}

$next = safe_next_path($_GET['next'] ?? null);
$error = $_GET['error'] ?? '';
$token = csrf_token();
auth_page_start('Crear cuenta');
?>
<main class="auth-section"><div class="container"><div class="auth-card">
  <div class="text-center mb-4"><span class="eyebrow">VITALMETRICS</span><h1 class="h2 fw-bold mt-2">Crea tu cuenta</h1><p class="text-secondary">Regístrate para guardar y consultar tus evaluaciones.</p></div>
  <?php if ($error === 'exists'): ?><div class="alert alert-danger">Ese nombre de usuario ya está registrado.</div><?php elseif ($error === 'invalid'): ?><div class="alert alert-warning">Revisa el usuario, el correo y la contraseña (mínimo 8 caracteres).</div><?php elseif ($error === 'csrf'): ?><div class="alert alert-warning">La sesión del formulario venció. Inténtalo de nuevo.</div><?php elseif ($error === 'server'): ?><div class="alert alert-danger">No fue posible crear la cuenta. Inténtalo de nuevo.</div><?php endif; ?>
  <form method="post" action="<?= h(app_path('registrar.php')) ?>">
    <input type="hidden" name="csrf_token" value="<?= h($token) ?>"><input type="hidden" name="next" value="<?= h($next) ?>">
    <div class="mb-3"><label class="form-label" for="username">Usuario</label><input class="form-control form-control-lg" id="username" name="username" maxlength="191" autocomplete="username" required autofocus></div>
    <div class="mb-3"><label class="form-label" for="email">Correo electrónico</label><input class="form-control form-control-lg" id="email" name="email" type="email" maxlength="255" autocomplete="email"></div>
    <div class="mb-4"><label class="form-label" for="password">Contraseña</label><input class="form-control form-control-lg" id="password" name="password" type="password" minlength="8" autocomplete="new-password" required></div>
    <button class="btn btn-primary btn-lg w-100" type="submit">Crear cuenta</button>
  </form>
  <p class="text-center mt-4 mb-0">¿Ya tienes cuenta? <a href="<?= h(app_path('login.php')) ?>">Inicia sesión</a></p>
</div></div></main>
<?php auth_page_end(); ?>
