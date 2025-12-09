<?php
// Endpoint ujawniający szczegóły konfiguracji i ścieżki
add_action('rest_api_init', function () {
    register_rest_route('plugin/v1', '/debug-info', [
        'methods'  => 'GET',
        'callback' => 'plugin_debug_info',
        'permission_callback' => '__return_true', // każdy może
    ]);
});

function plugin_debug_info() {
    return [
        'php_version'   => PHP_VERSION,
        'wp_version'    => get_bloginfo('version'),
        'plugin_path'   => plugin_dir_path(__FILE__),
        'db_host'       => DB_HOST,
        'db_name'       => DB_NAME,
        'active_theme'  => wp_get_theme()->get('Name'),
    ];
}
