/**
 * Lendlyfin - Google Forms App Script
 * 
 * Paste this into your Google Form's App Script editor:
 * Form → ⋮ → Script editor
 * 
 * Then set a trigger:
 * Triggers → Add Trigger → onFormSubmit → Form Submit
 */

var BACKEND_URL = "https://lendlyfin2-production.up.railway.app/api/leads/google-form";

function onFormSubmit(e) {
  var response = e.response;
  var itemResponses = response.getItemResponses();

  // Map question titles to named fields (cleaner than entry IDs)
  var titleToField = {
    "Full Name":             "full_name",
    "Email":                 "email",
    "Phone Number":          "phone",
    "Desired Loan Amount":   "loan_amount",
    "Loan Purpose":          "loan_purpose",
    "Property Type":         "property_type",
    "Current Credit Score":  "credit_score",
    "Employment Status":     "employment_status",
    "Additional Notes":      "additional_notes",
  };

  var payload = {};

  for (var i = 0; i < itemResponses.length; i++) {
    var item = itemResponses[i];
    var title = item.getItem().getTitle();
    var answer = item.getResponse();

    var fieldName = titleToField[title];
    if (fieldName) {
      payload[fieldName] = answer || "";
    }
  }

  // POST to backend
  var options = {
    method: "post",
    contentType: "application/json",
    payload: JSON.stringify(payload),
    muteHttpExceptions: true,
  };

  try {
    var result = UrlFetchApp.fetch(BACKEND_URL, options);
    Logger.log("Status: " + result.getResponseCode());
    Logger.log("Response: " + result.getContentText());
  } catch (err) {
    Logger.log("Error: " + err.toString());
  }
}
