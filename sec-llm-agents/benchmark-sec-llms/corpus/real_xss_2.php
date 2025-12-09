<?php
// Parametr GET przepisywany do atrybutu JS w inline script
function output_search_script() {
    $term = isset($_GET['term']) ? $_GET['term'] : '';

    ?>
    <script type="text/javascript">
        // podatne: bez json_encode/esc_js
        var initialSearch = '<?php echo $term; ?>';
        document.addEventListener('DOMContentLoaded', function() {
            document.getElementById('search').value = initialSearch;
        });
    </script>
    <?php
}
