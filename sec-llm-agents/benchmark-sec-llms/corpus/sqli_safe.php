<?php
// Bezpieczna wersja – powinna być oznaczona jako brak SQLi
function login_user_safe($username, $password) {
    global $wpdb;
    $sql = "SELECT * FROM {$wpdb->users} WHERE user_login = %s AND user_pass = %s";
    return $wpdb->get_results($wpdb->prepare($sql, $username, $password));
}
