<?php
// Celowo podatne SQLi
function login_user($username, $password) {
    global $wpdb;
    $sql = "SELECT * FROM {$wpdb->users} WHERE user_login = '$username' AND user_pass = '$password'";
    return $wpdb->get_results($sql);
}
