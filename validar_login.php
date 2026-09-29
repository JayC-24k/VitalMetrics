<?php
declare(strict_types=1);
require __DIR__ . '/php/private/bootstrap.php';

$next = safe_next_path($_POST['next'] ?? null);
if ($_SERVER['REQUEST_METHOD'] !== 'POST' || !valid_csrf_token()) {
    redirect_auth_error('login.php', 'csrf', $next);
}

$username = trim((string) ($_POST['username'] ?? ''));
$password = (string) ($_POST['password'] ?? '');
if ($username === '' || $password === '') {
    redirect_auth_error('login.php', 'invalid', $next);
}

try {
    $pdo = db();
    $statement = $pdo->prepare('SELECT id, username, password FROM users WHERE username = ? LIMIT 1');
    $statement->execute([$username]);
    $user = $statement->fetch();
    if (!$user || !password_verify_compatible($password, (string) $user['password'])) {
        redirect_auth_error('login.php', 'invalid', $next);
    }

    render_session_bridge(issue_login_ticket((int) $user['id'], $next));
} catch (PDOException | RuntimeException $error) {
    error_log('VitalMetrics PHP login failed: ' . $error->getMessage());
    redirect_auth_error('login.php', 'server', $next);
}
