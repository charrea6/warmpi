/*
 * Options:
 *      path:  Path to the API
 *      type:  POST/GET
 *      data:  Optional json data to send to server.
 *   success:  An optional success callback
 *   failure:  An optional error callback
 */

function apiRequest(options){
    if (options.data !== undefined){
        data = $.toJSON(options.data);
    } else {
        data = undefined;
    }
    setup = {
        type: options.type || 'GET',
        dataType: 'json',
        data:data,
        contentType: 'application/json; charset=UTF-8',

        success: function(data, textStatus, jqXHR) {
            cb = options.success;
            if (cb !== undefined){
                cb(data);
            }
        },

        error: function(jqXHR, textStatus, errorThrown){
            cb = options.failure;
            if (cb !== undefined){
                cb();
            }
        }
    };
    $.ajax('/api/' + options.path, setup);
}

/*
 * Status
 */

function status_GetInfo(on){
    apiRequest({path:'info', success:on.success, failure: on.failure});
}

/*
 * Relay Subsystem
 */

function relay_GetAllStates(on){
    apiRequest({path:'relay', success: on.success, failure: on.failure});
}

function relay_GetState(relay, on){
    apiRequest({path:'relay/' + relay, success: on.success, failure: on.failure});
}

function relay_SetState(relay, enabled, on){
    on = on || {};
    apiRequest({path:'relay/' + relay, type:'POST', data:{'active':enabled}, success: on.success, failure: on.failure});
}

/*
 * Thermostat subsystem
 */

function thermostat_GetAllThermostats(on){
    apiRequest({path:'thermostat', success: on.success, failure: on.failure});
}

function thermostat_GetThermostat(thermostat, on){
    apiRequest({path:'thermostat/' + thermostat, success: on.success, failure: on.failure});
}

function thermostat_GetThermostatProp(thermostat, prop, on){
    apiRequest({path:'thermostat/' + thermostat + '/' + prop, success: on.success, failure: on.failure});
}

function thermostat_SetThermostatProp(thermostat, prop, value, on){
    var data = {};
    data[prop] = value;
    apiRequest({type:'POST', path:'thermostat/' + thermostat + '/' + prop, data:data, success: on.success, failure: on.failure});
}

function thermostat_SetZoneSetpoint(zone, setpoint, on){
    apiRequest({type:'POST', path:'thermostat', data:{'zone':zone, 'setpoint':setpoint}, success: on.success, failure: on.failure});
}

/*
 * Schedule Subsystem
 */
function schedule_GetInfo(on){
    apiRequest({path:'schedule', success:on.success, failure: on.failure});
}
