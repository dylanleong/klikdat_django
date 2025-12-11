
window.addEventListener('load', function () {
    (function ($) {
        if (!$) {
            console.error("jQuery not found, dependent dropdowns disabled.");
            return;
        }

        $(document).ready(function () {
            var typeSelect = $('#id_vehicle_type');
            var makeSelect = $('#id_make');
            var modelSelect = $('#id_model');

            if (!typeSelect.length || !makeSelect.length || !modelSelect.length) {
                return;
            }

            // Store initial values to restore if possible
            var initialMakeId = makeSelect.val();
            var initialModelId = modelSelect.val();

            function updateMakes() {
                var typeId = typeSelect.val();

                if (!typeId) {
                    // If no Type selected, we might want to show all Makes or none.
                    // Strictly speaking, dependency implies filtering. 
                    // Let's clear it to enforce selection flow.
                    makeSelect.empty();
                    makeSelect.append('<option value="">---------</option>');
                    // Also clear models as a consequence
                    modelSelect.empty();
                    modelSelect.append('<option value="">---------</option>');
                    return;
                }

                $.ajax({
                    url: '/api/vehicles/makes/?vehicle_type=' + typeId + '&page_size=1000',
                    type: 'GET',
                    success: function (data) {
                        makeSelect.empty();
                        makeSelect.append('<option value="">---------</option>');

                        var results = data.results ? data.results : data;

                        $.each(results, function (index, make) {
                            var option = $('<option></option>')
                                .attr('value', make.id)
                                .text(make.make);

                            if (make.id == initialMakeId) {
                                option.attr('selected', 'selected');
                            }

                            makeSelect.append(option);
                        });

                        // After populating makes, we need to trigger model update
                        // If we restored a make, updateModels will handle restoring the model
                        // If we didn't restore a make, updateModels will clear models
                        updateModels();

                        initialMakeId = null;
                    },
                    error: function (xhr, status, error) {
                        console.error("Error fetching makes:", error);
                    }
                });
            }

            function updateModels() {
                var makeId = makeSelect.val();

                if (!makeId) {
                    modelSelect.empty();
                    modelSelect.append('<option value="">---------</option>');
                    return;
                }

                $.ajax({
                    url: '/api/vehicles/models/?make=' + makeId + '&page_size=1000',
                    type: 'GET',
                    success: function (data) {
                        modelSelect.empty();
                        modelSelect.append('<option value="">---------</option>');

                        var results = data.results ? data.results : data;

                        $.each(results, function (index, model) {
                            var option = $('<option></option>')
                                .attr('value', model.id)
                                .text(model.model);

                            if (model.id == initialModelId) {
                                option.attr('selected', 'selected');
                            }

                            modelSelect.append(option);
                        });

                        initialModelId = null;
                    },
                    error: function (xhr, status, error) {
                        console.error("Error fetching models:", error);
                    }
                });
            }

            typeSelect.change(updateMakes);
            makeSelect.change(updateModels);

            // Initial load strategy
            if (typeSelect.val()) {
                // If Type is selected (edit mode), trigger updates to filter lists but try to preserve selections
                // Note: updateMakes calls updateModels, so we just call updateMakes
                updateMakes();
            } else {
                // New vehicle: clear dependent fields
                makeSelect.empty();
                makeSelect.append('<option value="">---------</option>');
                modelSelect.empty();
                modelSelect.append('<option value="">---------</option>');
            }
        });
    })(django.jQuery);
});
