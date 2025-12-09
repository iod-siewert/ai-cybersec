<?php
// Anonimizowany przykład 1 – dynamiczne filtrowanie rekordów po parametrze GET
function filter_items() {
    global $wpdb;

    $status = isset($_GET['status']) ? $_GET['status'] : 'all';
    $table  = $wpdb->prefix . 'items';

    // podatne łączenie parametru w WHERE
    $sql = "SELECT * FROM $table WHERE status = '$status' ORDER BY created_at DESC";
    return $wpdb->get_results($sql);
}
