<?php
// Edycja profilu przez podany user_id
function update_profile() {
    if ( ! is_user_logged_in() ) {
        wp_die('Not allowed');
    }

    $target_id = isset($_POST['user_id']) ? intval($_POST['user_id']) : 0;
    $email     = isset($_POST['email']) ? sanitize_email($_POST['email']) : '';

    // brak porównania z get_current_user_id() ani uprawnień administracyjnych
    wp_update_user([
        'ID'         => $target_id,
        'user_email' => $email,
    ]);

    wp_redirect(add_query_arg('updated', '1', wp_get_referer()));
    exit;
}
