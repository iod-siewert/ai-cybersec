<?php
// Poprawna obsługa z check_ajax_referer
add_action('wp_ajax_delete_item_safe', 'my_delete_item_safe');

function my_delete_item_safe() {
    check_ajax_referer('delete-item-nonce', 'nonce');

    $id = intval($_POST['id']);
    wp_delete_post($id, true);
    wp_send_json_success();
}