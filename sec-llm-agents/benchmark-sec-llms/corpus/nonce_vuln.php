<?php
// AJAX bez nonce – Broken Access Control
add_action('wp_ajax_delete_item', 'my_delete_item');

function my_delete_item() {
    $id = intval($_POST['id']);
    wp_delete_post($id, true);
    wp_send_json_success();
}
