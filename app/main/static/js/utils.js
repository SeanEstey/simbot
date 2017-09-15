/* utils.js 
   String-related utility functions.
*/

function getElapsedTime(t1) {
    var d = new Date();
    return new Date().getTime() - t1.getTime();
}

//---------------------------------------------------------------------
function format(str) {
  /* str: "Hello %s, my name is %s" 
     args: one for each %s 
  */ 

  var args = [].slice.call(arguments, 1), i = 0;
  return str.replace(/%s/g, function() {return args[i++];});
}

//------------------------------------------------------------------------------
String.prototype.toTitleCase = function(n) {
  // Replace underscores with spaces, capitalizes words

   var s = this;
   if (1 !== n) 
     s = s.toLowerCase();
   s = s.replace(/_/g, ' ');
   return s.replace(/\b[a-z]/g,function(f){return f.toUpperCase()});
}


//------------------------------------------------------------------------------
function toElapsedStr(ms) {

    if(ms < 1000)
        return format("%s ms", ms);
    else if(ms >= 1000 && ms < 60000)
        return format('%s sec', (ms/1000).toFixed(1));
    else if(ms >= 60000)
        return format('%s min', (ms/60000).toFixed(1));
}

//------------------------------------------------------------------------------
function toRelativeDateStr(date) {

    var now = new Date();
    var diff_ms = now.getTime() - date.getTime();
    
    var min_ms = 1000 * 60;
    var hour_ms = 1000 * 3600;
    var day_ms = hour_ms * 24;
    var week_ms = day_ms * 7;
    var month_ms = day_ms * 30;
    var year_ms = day_ms * 365;

    if(diff_ms >= year_ms) {
        // Year(s) span
        var nYears = Number((diff_ms/year_ms).toFixed(0));
        return format("%s year%s ago", nYears, nYears > 1 ? 's' : '');
    }

    if(diff_ms >= month_ms) {
        // Month(s) span
        var nMonths = Number((diff_ms/month_ms).toFixed(0));
        return format("%s month%s ago", nMonths, nMonths > 1 ? 's' : '');
    }

    if(diff_ms >= week_ms) {
        // Week(s) span
        var nWeeks = Number((diff_ms/week_ms).toFixed(0));
        return format("%s week%s ago", nWeeks, nWeeks > 1 ? 's' : '');
    }
    
    if(diff_ms >= day_ms) {
        // Day(s) span
        var nDays = Number((diff_ms/day_ms).toFixed(0));
        return format("%s day%s ago", nDays, nDays > 1 ? 's' : '');
    }

    if(diff_ms >= hour_ms) {
        // Hour(s) span
        var nHours = Number((diff_ms/hour_ms).toFixed(0));
        return format("%s hour%s ago", nHours, nHours > 1 ? 's' : '');
    }

    if(diff_ms >= min_ms) {
        // Minute(s) span
        var nMin = Number((diff_ms/min_ms).toFixed(0));
        return format("%s min ago", nMin);
    }

    // Second(s) span
    var nSec = Number((diff_ms/1000).toFixed(0));
    return format("%s second%s ago", nSec, nSec > 1 ? 's' : '');
}

//------------------------------------------------------------------------------
function HTMLEncode(str) {
  // Returns decimal code for special HTML characters

  var i = str.length,
    aRet = [];

  while (i--) {
    var iC = str[i].charCodeAt();
    if (iC < 65 || iC > 127 || (iC > 90 && iC < 97)) {
      aRet[i] = '&#' + iC + ';';
    } else {
      aRet[i] = str[i];
    }
  }
  return aRet.join('');
}
