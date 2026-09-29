<?php
declare(strict_types=1);
require __DIR__ . '/php/private/bootstrap.php';
begin_php_session();

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    if (!valid_csrf_token()) {
        http_response_code(400);
        exit('La sesión del formulario venció. Vuelve a cargar esta página.');
    }
    $_SESSION = [];
    session_destroy();
    auth_page_start('Cerrando sesión');
    echo '<main class="container py-5"><p class="text-center">Cerrando sesión…</p>';
    echo '<form id="logout" method="post" action="' . h(app_path('logout')) . '">';
    echo '<noscript><button class="btn btn-primary">Continuar</button></noscript></form>';
    echo '<script>document.getElementById("logout").submit();</script></main>';
    auth_page_end();
    exit;
}

$token = csrf_token();
auth_page_start('Cerrar sesión');
?>
<main class="container py-5 text-center"><h1 class="h3">¿Quieres cerrar sesión?</h1>
  <form method="post" action="<?= h(app_path('logout.php')) ?>" class="mt-4">
    <input type="hidden" name="csrf_token" value="<?= h($token) ?>">
    <button class="btn btn-primary" type="submit">Cerrar sesión</button>
    <a class="btn btn-outline-secondary" href="<?= h(app_path()) ?>">Cancelar</a>
  </form>
</main>
<?php auth_page_end(); ?>
