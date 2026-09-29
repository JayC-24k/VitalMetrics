<?php
declare(strict_types=1);

function app_config(): array
{
    static $config;
    if (isset($config)) {
        return $config;
    }

    $config = [];
    $envFile = dirname(__DIR__, 2) . DIRECTORY_SEPARATOR . '.env';
    if (is_file($envFile)) {
        foreach (file($envFile, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES) ?: [] as $line) {
            $line = trim($line);
            if ($line === '' || str_starts_with($line, '#') || !str_contains($line, '=')) {
                continue;
            }
            [$key, $value] = explode('=', $line, 2);
            $key = trim($key);
            $value = trim(trim($value), "\"'");
            if ($key !== '') {
                $config[$key] = getenv($key) !== false ? (string) getenv($key) : $value;
            }
        }
    }

    return $config;
}

function app_base_path(): string
{
    $path = str_replace('\\', '/', dirname($_SERVER['SCRIPT_NAME'] ?? '/'));
    return $path === '/' || $path === '.' ? '' : rtrim($path, '/');
}

function app_path(string $path = ''): string
{
    $base = app_base_path();
    return $base . ($path === '' ? '/' : '/' . ltrim($path, '/'));
}

function h(?string $value): string
{
    return htmlspecialchars($value ?? '', ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}

function db(): PDO
{
    static $pdo;
    if (isset($pdo)) {
        return $pdo;
    }

    $config = app_config();
    $engine = strtolower($config['DB_ENGINE'] ?? 'mysql');
    if (!in_array($engine, ['mysql', 'mariadb'], true)) {
        throw new RuntimeException('La autenticación PHP requiere DB_ENGINE=mysql en .env.');
    }

    $host = $config['MYSQL_HOST'] ?? '127.0.0.1';
    $port = $config['MYSQL_PORT'] ?? '3306';
    $database = $config['MYSQL_DATABASE'] ?? 'vitalmetrics';
    $pdo = new PDO(
        "mysql:host={$host};port={$port};dbname={$database};charset=utf8mb4",
        $config['MYSQL_USER'] ?? 'root',
        $config['MYSQL_PASSWORD'] ?? '',
        [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            PDO::ATTR_EMULATE_PREPARES => false,
        ]
    );
    $pdo->exec(
        "CREATE TABLE IF NOT EXISTS php_login_tickets (
            token_hash CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL PRIMARY KEY,
            user_id INT NOT NULL,
            redirect_to VARCHAR(2048) NOT NULL,
            expires_at DATETIME NOT NULL,
            INDEX idx_php_login_tickets_expiry (expires_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci"
    );

    return $pdo;
}

function begin_php_session(): void
{
    if (session_status() === PHP_SESSION_ACTIVE) {
        return;
    }
    session_set_cookie_params([
        'httponly' => true,
        'secure' => !empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off',
        'samesite' => 'Lax',
        'path' => app_base_path() ?: '/',
    ]);
    session_start();
}

function csrf_token(): string
{
    begin_php_session();
    if (empty($_SESSION['csrf_token'])) {
        $_SESSION['csrf_token'] = bin2hex(random_bytes(32));
    }
    return $_SESSION['csrf_token'];
}

function valid_csrf_token(): bool
{
    begin_php_session();
    $submitted = $_POST['csrf_token'] ?? '';
    return is_string($submitted)
        && isset($_SESSION['csrf_token'])
        && hash_equals($_SESSION['csrf_token'], $submitted);
}

function password_hash_compatible(string $password): string
{
    $iterations = 260000;
    $salt = random_bytes(16);
    $digest = hash_pbkdf2('sha256', $password, $salt, $iterations, 64);
    return 'pbkdf2_sha256$' . $iterations . '$' . bin2hex($salt) . '$' . $digest;
}

function password_verify_compatible(string $password, string $stored): bool
{
    $parts = explode('$', $stored);
    if (count($parts) === 4 && $parts[0] === 'pbkdf2_sha256') {
        $iterations = filter_var($parts[1], FILTER_VALIDATE_INT, ['options' => ['min_range' => 1]]);
        if ($iterations === false || !preg_match('/\A[0-9a-fA-F]{32,}\z/', $parts[2])
            || !preg_match('/\A[0-9a-fA-F]{64}\z/', $parts[3])) {
            return false;
        }
        $digest = hash_pbkdf2('sha256', $password, hex2bin($parts[2]), $iterations, 64);
        return hash_equals(strtolower($parts[3]), strtolower($digest));
    }

    return hash_equals($stored, hash('sha256', $password)) || hash_equals($stored, $password);
}

function safe_next_path(?string $candidate): string
{
    $base = app_base_path();
    $fallback = app_path();
    if (!$candidate || !str_starts_with($candidate, '/') || str_starts_with($candidate, '//')) {
        return $fallback;
    }
    if ($base !== '' && $candidate !== $base && !str_starts_with($candidate, $base . '/')) {
        return $fallback;
    }
    return $candidate;
}

function issue_login_ticket(int $userId, ?string $next): string
{
    $pdo = db();
    $pdo->exec('DELETE FROM php_login_tickets WHERE expires_at <= CURRENT_TIMESTAMP');
    $ticket = bin2hex(random_bytes(32));
    $statement = $pdo->prepare(
        'INSERT INTO php_login_tickets (token_hash, user_id, redirect_to, expires_at)
         VALUES (?, ?, ?, DATE_ADD(CURRENT_TIMESTAMP, INTERVAL 2 MINUTE))'
    );
    $statement->execute([hash('sha256', $ticket), $userId, safe_next_path($next)]);
    return $ticket;
}

function redirect_auth_error(string $page, string $error, ?string $next = null): never
{
    $query = ['error' => $error];
    if ($next) {
        $query['next'] = safe_next_path($next);
    }
    header('Location: ' . app_path($page) . '?' . http_build_query($query), true, 303);
    exit;
}

function render_session_bridge(string $ticket): never
{
    $action = app_path('auth/php-session');
    $ticket = h($ticket);
    $action = h($action);
    header('Content-Type: text/html; charset=utf-8');
    echo '<!doctype html><html lang="es"><meta charset="utf-8"><title>Iniciando sesión</title>';
    echo '<body><form id="bridge" method="post" action="' . $action . '">';
    echo '<input type="hidden" name="ticket" value="' . $ticket . '">';
    echo '<noscript><button type="submit">Continuar</button></noscript></form>';
    echo '<script>document.getElementById("bridge").submit();</script></body></html>';
    exit;
}

function auth_page_start(string $title): void
{
    $base = h(app_base_path());
    echo '<!doctype html><html lang="es"><head><meta charset="utf-8">';
    echo '<meta name="viewport" content="width=device-width, initial-scale=1">';
    echo '<title>' . h($title) . ' | VitalMetrics</title>';
    echo '<link rel="stylesheet" href="' . $base . '/static/vendor/bootstrap/css/bootstrap.min.css">';
    echo '<link rel="stylesheet" href="' . $base . '/static/css/app.css"></head><body>';
    echo '<nav class="navbar vm-navbar"><div class="container"><a class="navbar-brand" href="' . $base . '/">VitalMetrics</a></div></nav>';
}

function auth_page_end(): void
{
    echo '<script src="' . h(app_base_path()) . '/static/vendor/bootstrap/js/bootstrap.bundle.min.js"></script>';
    echo '</body></html>';
}
