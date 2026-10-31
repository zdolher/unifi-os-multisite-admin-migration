// Read-only export for the NEW UniFi Network app's `ace` MongoDB.
// Run via mongo shell in the UniFi OS Server container, redirect stdout to target_sites.jsonl.
// WARNING: the output contains private site descriptions. DO NOT publish it.
(function () {
    function key(v) {
        if (v && typeof v.str === 'string') return v.str;
        if (typeof v === 'string') return v;
        return String(v);
    }
    var count = 0;
    db.site.find({}, {_id: 1, name: 1, desc: 1}).forEach(function(s) {
        print(JSON.stringify({site_id: key(s._id), site_name: s.name || '', site_description: s.desc || ''}));
        count++;
    });
    if (count === 0 || count !== db.site.count()) throw new Error('Incomplete site export');
    print(JSON.stringify({_export_summary: true, site_count: count}));
}());
