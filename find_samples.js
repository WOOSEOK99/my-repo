const fs = require('fs');
const path = require('path');

const target_samples = [
    "005", "3bagfull", "astrof", "battles", "bbc", "blockade", "bowl3d",
    "circus", "clowns", "cosmica", "cosmicg", "crash", "dai3wksi", "depthch",
    "equites", "fantasy", "fruitsamples", "ftaerobi", "gaplus", "genpin", "gmissile",
    "gridlee", "homerun", "ifslots", "ipminvad", "journey", "kst25", "ktmnt2", "ktopgun2",
    "lrescue", "lupin3", "mmagic", "moepro", "moepro88", "moepro90", "monsterb",
    "mpsaikyo", "mptennis", "natodef", "nsub", "ozmawars", "panic", "ptrmj",
    "redclash", "relay", "ripcord", "robotbwl", "safarir", "sasuke", "sharkatt",
    "smoepro", "spacefb", "spaceod", "tattack", "terao", "thehand", "thief",
    "triplhnt", "turbo", "twotiger", "zerohour"
];

const src_dir = "D:\\301_GUI\\apps\\core\\mame-2003-plus-kaze\\src";

let files_content = {};

function walkSync(dir) {
    const files = fs.readdirSync(dir);
    for (const file of files) {
        const fullPath = path.join(dir, file);
        const stat = fs.statSync(fullPath);
        if (stat.isDirectory()) {
            walkSync(fullPath);
        } else {
            if (file.endsWith('.c') || file.endsWith('.h') || file.endsWith('.cpp')) {
                try {
                    files_content[fullPath] = fs.readFileSync(fullPath, 'utf-8');
                } catch(e) {}
            }
        }
    }
}
walkSync(src_dir);

const final_mappings = [];

for (const ts of target_samples) {
    let array_name = null;
    let array_file = null;
    
    const p1 = new RegExp('([A-Za-z0-9_]+)\\s*\\[\\]\\s*=\\s*\\{[^}]*"\\*' + ts + '"', 'm');
    for (const [filepath, content] of Object.entries(files_content)) {
        const m = p1.exec(content);
        if (m) {
            array_name = m[1];
            array_file = filepath;
            break;
        }
    }
    
    if (!array_name) {
        const p1b = new RegExp('([A-Za-z0-9_]+).*"{1}\\*' + ts + '"{1}');
        for (const [filepath, content] of Object.entries(files_content)) {
            const m = p1b.exec(content);
            if (m) {
                array_name = m[1];
                array_file = filepath;
                break;
            }
        }
    }

    if (!array_name) {
        final_mappings.push([ts, ts]);
        continue;
    }

    let interface_names = new Set([array_name]);
    const p2 = new RegExp('([A-Za-z0-9_]+)\\s*=\\s*\\{[^}]*' + array_name + '[^}]*\\}', 'g');
    for (const [filepath, content] of Object.entries(files_content)) {
        let m;
        while ((m = p2.exec(content)) !== null) {
            interface_names.add(m[1]);
        }
    }
    
    let machine_names = new Set();
    const p3 = /(?:MACHINE_DRIVER_START|MACHINE_CONFIG_START)\s*\(\s*([A-Za-z0-9_]+)\s*\)([\s\S]*?)(?:MACHINE_DRIVER_START|MACHINE_CONFIG_START|GAME|$)/g;
    for (const [filepath, content] of Object.entries(files_content)) {
        let m;
        while ((m = p3.exec(content)) !== null) {
            const mach = m[1];
            const body = m[2];
            for (const itf of interface_names) {
                if (body.includes(itf)) {
                    machine_names.add(mach);
                }
            }
        }
    }
    
    let games = new Set();
    const p4 = /(?:GAME|GAMEX|COMP|CONS|SYST)\s*\(\s*[^,]+,\s*([^, \t\r\n]+),\s*([^, \t\r\n]+),\s*([^, \t\r\n\)]+)/g;
    for (const [filepath, content] of Object.entries(files_content)) {
        let m;
        while ((m = p4.exec(content)) !== null) {
            const g_name = m[1].trim();
            const g_mach = m[3].trim();
            if (machine_names.has(g_mach)) {
                games.add(g_name);
            }
        }
    }
    
    if (games.size > 0) {
        for (const g of games) {
            final_mappings.push([g, ts]);
        }
    } else {
        const content = files_content[array_file] || "";
        const p5 = /(?:GAME|GAMEX|COMP|CONS|SYST)\s*\(\s*[^,]+,\s*([^, \t\r\n]+)/g;
        let m;
        let fallback_games = new Set();
        while ((m = p5.exec(content)) !== null) {
            fallback_games.add(m[1].trim());
        }
        if (fallback_games.size > 0) {
            for (const g of fallback_games) {
                final_mappings.push([g, ts]);
            }
        } else {
            final_mappings.push([ts, ts]);
        }
    }
}

let res_dict = {};
for (const [g, s] of final_mappings) {
    if (g && s) {
        res_dict[g] = s;
    }
}

fs.writeFileSync('final_mappings.json', JSON.stringify(res_dict, null, 4));
