<?php
// ID użytkownika brany bezpośrednio z GET, brak sprawdzenia właściciela
function download_invoice() {
    if ( ! is_user_logged_in() ) {
        wp_die('Not allowed');
    }

    $invoice_id = isset($_GET['invoice_id']) ? intval($_GET['invoice_id']) : 0;
    if ( ! $invoice_id ) {
        wp_die('Missing id');
    }

    global $wpdb;
    $table = $wpdb->prefix . 'invoices';
    // brak sprawdzenia, czy faktura należy do current_user()
    $invoice = $wpdb->get_row( $wpdb->prepare("SELECT * FROM $table WHERE id = %d", $invoice_id) );
    if ( ! $invoice ) {
        wp_die('Not found');
    }

    header('Content-Type: application/pdf');
    echo $invoice->pdf_content;
    exit;
}
