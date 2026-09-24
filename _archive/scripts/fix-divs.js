const fs = require('fs');

const files = [
    'webapp/static/dsa-viz11.js',
    'webapp/static/dsa-viz12.js',
    'webapp/static/dsa-viz13.js',
    'webapp/static/dsa-viz14.js',
    'webapp/static/dsa-viz15.js',
    'webapp/static/dsa-viz4.js',
    'webapp/static/dsa-viz5.js',
    'webapp/static/dsa-viz7.js',
    'webapp/static/dsa-viz8.js',
    'webapp/static/dsa-viz9.js',
    'webapp/static/dsa-viz10.js'
];

files.forEach(file => {
    if (!fs.existsSync(file)) return;
    let content = fs.readFileSync(file, 'utf8');

    let oldContent = content;
    
    // Replace:
    // <div class="node-index">...</div>
    //     `;
    // With:
    // <div class="node-index">...</div>
    //             </div>
    //     `;
    
    content = content.replace(/(<div class="node-index"[^>]*>.*?<\/div>)\n\s*`;/g, '$1\n            </div>`;');
    
    // There are some places that didn't have node-index, like getPathHTML, getResultsHTML, which also got broken.
    // Let's just fix those by matching the broken template literals returning array-node.
    // Wait, getPathHTML in dsa-viz11.js:
    // return path.map(val => `
    //         <div class="array-node active-1" ...>
    //             ${val}
    //         </div>
    // `).join('');
    // Wait, did getPathHTML get broken? No, because it didn't end with </div> </div> `;
    
    if (oldContent !== content) {
        fs.writeFileSync(file, content);
        console.log("Fixed missing div in", file);
    }
});
