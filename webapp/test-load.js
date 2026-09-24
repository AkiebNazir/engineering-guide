const fs = require('fs');
const jsdom = require("jsdom");
const { JSDOM } = jsdom;
const dom = new JSDOM("<!DOCTYPE html><html><body></body></html>", { runScripts: "dangerously" });
const window = dom.window;

window.avNums = () => [];
window.avParts = () => [];
window.avNum = () => 0;
window.console = console;

let allCode = fs.readFileSync('static/dsa-viz.js', 'utf8') + '\n' +
              fs.readFileSync('static/dsa-viz-dom.js', 'utf8') + '\n' +
              fs.readFileSync('static/viz-algorithms.js', 'utf8') + '\n' +
              `console.log("ALGOS 27_algorithms length:", ALGOS['27_algorithms'].length);
               ALGOS['27_algorithms'].forEach(a => console.log(a.title));`;

try {
    window.eval(allCode);
} catch(e) {
    console.error("ERROR:", e);
}
