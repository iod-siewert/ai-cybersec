<?php
// Anonimizowany przykład 2 – wyszukiwanie z parametrem POST
function search_items() {
    global $wpdb;

    $q = isset($_POST['q']) ? $_POST['q'] : '';
    $table  = $wpdb->prefix . 'items';

    // brak prepare(), wildcard + concat
    $sql = "SELECT * FROM $table WHERE title LIKE '%$q%' OR description LIKE '%$q%'";
    return $wpdb->get_results($sql);
}
