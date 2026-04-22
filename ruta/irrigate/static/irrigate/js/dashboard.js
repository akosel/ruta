(function () {
	"use strict";

	var formatOptions = {
		time: {
			hour: "numeric",
			minute: "2-digit",
		},
		datetime: {
			month: "short",
			day: "numeric",
			hour: "numeric",
			minute: "2-digit",
		},
		weekday: {
			weekday: "long",
		},
		"weekday-time": {
			weekday: "long",
			hour: "numeric",
			minute: "2-digit",
		},
	};
	var timezoneFormatter = new Intl.DateTimeFormat(undefined, {
		timeZoneName: "short",
	});

	function getTimezoneName(date) {
		var parts = timezoneFormatter.formatToParts(date);
		for (var index = 0; index < parts.length; index += 1) {
			if (parts[index].type === "timeZoneName") {
				return parts[index].value;
			}
		}
		return "";
	}

	function localizeTimeElement(element) {
		var date = new Date(element.getAttribute("datetime"));
		var format = element.dataset.dashboardFormat;

		if (Number.isNaN(date.getTime()) || !formatOptions[format]) {
			return;
		}

		element.textContent = new Intl.DateTimeFormat(
			undefined,
			formatOptions[format]
		).format(date);

		var timezoneName = getTimezoneName(date);
		if (timezoneName) {
			element.title = "Shown in your local timezone (" + timezoneName + ")";
		}
	}

	document
		.querySelectorAll("time[data-dashboard-format]")
		.forEach(localizeTimeElement);
})();
