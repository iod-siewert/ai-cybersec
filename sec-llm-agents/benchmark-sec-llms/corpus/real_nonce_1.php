<?php
// Formularz w panelu bez nonce, akcja modyfikuje dane
function render_settings_form() {
    ?>
    <form method="post" action="">
        <input type="text" name="api_key" value="" />
        <button type="submit" name="save_settings" value="1">Save</button>
    </form>
    <?php
}

function handle_settings_form() {
    if ( isset($_POST['save_settings']) ) {
        // brak check_admin_referer / wp_verify_nonce
        $api_key = sanitize_text_field($_POST['api_key']);
        update_option('plugin_remote_api_key', $api_key);
    }
}
add_action('admin_init', 'handle_settings_form');
