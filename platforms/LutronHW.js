var types = require("HAP-NodeJS/accessories/types.js");
var lutron = require("lutronhw/lutronHW.js");

function LutronHWPlatform(log, config){

    this.name = config["name"];
    this.connection = {
        host: config["ip_address"],
        port: config["port"],
        username: config["username"],
        password: config["password"]
    };
    this.rooms = config["rooms"];
    this.log = log;
}

LutronHWPlatform.prototype = {
    accessories: function(callback) {
        this.log("Fetching Lutron Homeworks devices.");

        var that = this;
        var foundAccessories = [];

        for (var i=0; i<this.rooms.length; i++) {
            var room = this.rooms[i].name;
            for (var j=0; j<this.rooms[i].things.length; j++) {
                var device = this.rooms[i].things[j];
                var accessory = new LutronHWAccessory(that.log, room, device);
                foundAccessories.push(accessory);
            }
        }

        lutron.init(this.connection, function() {callback(foundAccessories)});
    }
};

function LutronHWAccessory(log, room, device) {
    // device info
    this.name = room + " " + device.location + " " + device.type;
    this.device = device;
    this.log = log;
    this.powerState = 'Off';
    this.brightness = 0;
}

LutronHWAccessory.prototype = {
    getPowerState: function(callback){
        var that = this;

        this.log("Checking power state for: " + this.name);
        lutron.getLight(this.device.code, function(err, result) {
            if (result == null) {
                that.log("Power state for " + that.name + " can't be retrieved: " + err);
            } else {
                that.log("Power state for " + that.name + " is: " + (result != 0));
                callback((result != 0));
            }
        });
    },

    getBrightness: function(callback){
        var that = this;

        this.log("Checking brightness for: " + this.name);
        lutron.getLight(this.device.code, function(err, result) {
            if (result == null) {
                that.log("Brightness for " + that.name + " can't be retrieved: " + err);
            } else {
                that.log("Brightness  for " + that.name + " is: " + result);
                callback(result);
            }
        });
    },

    setPowerState: function(powerOn) {
        var that = this;

        if (powerOn) {
            this.log("Setting power state for: " + this.name + " to on");
            lutron.setLight(this.device.code, this.device.maxLevel || 100, function(err, result) {
                if (result == null) {
                    that.log("Error setting power state for " + that.name);
                } else {
                    that.log("Successfully set power state for " + that.name + " to on")
                }
            })
        } else {
            this.log("Setting power state for: " + this.name + " to off");
            lutron.setLight(this.device.code, 0, function (err, result) {
                if (result == null) {
                    that.log("Error setting power state for " + that.name);
                } else {
                    that.log("Successfully set power state for " + that.name + " to off")
                }
            })
        }
    },

    setBrightness: function(level) {
        var that = this;

        this.log("Setting brightness for: " + this.name + " to " + (this.device.maxLevel ||  level));
        lutron.setLight(this.device.code, ((this.device.maxLevel) ? Math.min(this.device.maxLevel, level) : level), function(err, result) {
            if (result == null) {
                that.log("Error setting brightness for " + that.name);
            } else {
                that.log("Successfully set brightness for " + that.name + " to " + ((that.device.maxLevel) ? Math.min(that.device.maxLevel, level) : level))
            }
        })
    },

    getServices: function() {
        var that = this;
        return [{
            sType: types.ACCESSORY_INFORMATION_STYPE,
            characteristics: [{
                cType: types.NAME_CTYPE,
                onUpdate: null,
                perms: ["pr"],
                format: "string",
                initialValue: this.name,
                supportEvents: false,
                supportBonjour: false,
                manfDescription: "Name of the accessory",
                designedMaxLength: 255
            },{
                cType: types.MANUFACTURER_CTYPE,
                onUpdate: null,
                perms: ["pr"],
                format: "string",
                initialValue: "Lutron",
                supportEvents: false,
                supportBonjour: false,
                manfDescription: "Manufacturer",
                designedMaxLength: 255
            },{
                cType: types.MODEL_CTYPE,
                onUpdate: null,
                perms: ["pr"],
                format: "string",
                initialValue: "Rev-1",
                supportEvents: false,
                supportBonjour: false,
                manfDescription: "Model",
                designedMaxLength: 255
            },{
                cType: types.SERIAL_NUMBER_CTYPE,
                onUpdate: null,
                perms: ["pr"],
                format: "string",
                initialValue: "A1S2NASF88EW",
                supportEvents: false,
                supportBonjour: false,
                manfDescription: "SN",
                designedMaxLength: 255
            },{
                cType: types.IDENTIFY_CTYPE,
                onUpdate: null,
                perms: ["pw"],
                format: "bool",
                initialValue: false,
                supportEvents: false,
                supportBonjour: false,
                manfDescription: "Identify Accessory",
                designedMaxLength: 1
            }]
        },{
            sType: types.LIGHTBULB_STYPE,
            characteristics: [{
                cType: types.NAME_CTYPE,
                onUpdate: null,
                perms: ["pr"],
                format: "string",
                initialValue: this.name,
                supportEvents: true,
                supportBonjour: false,
                manfDescription: "Name of service",
                designedMaxLength: 255
            },{
                cType: types.POWER_STATE_CTYPE,
                onUpdate: function(value) {
                    that.setPowerState(value);
                },
                onRead: function(callback) {
                    that.getPowerState(function(powerState){
                        callback(powerState);
                    });
                },
                perms: ["pw","pr","ev"],
                format: "bool",
                initialValue: 0,
                supportEvents: true,
                supportBonjour: false,
                manfDescription: "Change the power state of the Bulb/Shade",
                designedMaxLength: 1
            },{
                cType: types.BRIGHTNESS_CTYPE,
                onUpdate: function(value) {
                    that.setBrightness(value);
                },
                onRead: function(callback) {
                    that.getBrightness(function(level){
                        callback(level);
                    });
                },
                perms: ["pw","pr","ev"],
                format: "int",
                initialValue:  0,
                supportEvents: true,
                supportBonjour: false,
                manfDescription: "Adjust Brightness of Light/Shade",
                designedMinValue: 0,
                designedMaxValue: 100,
                designedMinStep: 1,
                unit: "%"
            }]
        }];
    }
};

module.exports.accessory = LutronHWAccessory;
module.exports.platform = LutronHWPlatform;