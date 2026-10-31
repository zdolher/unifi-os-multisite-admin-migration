// Read-only export for the legacy UniFi Network `ace` MongoDB.
// Run inside mongo shell: mongo --quiet --host 127.0.0.1 --port 27117 ace export_legacy.js > legacy_privileges.jsonl
// WARNING: the output contains private names, emails and site descriptions. DO NOT publish it.
// DO NOT run on any database other than the OLD legacy controller DB.
(function () {
    function key(v) {
        if (v && typeof v.str === 'string') return v.str;
        if (typeof v === 'string') return v;
        return String(v);
    }
    var admins = {}, sites = {}, count = 0;
    db.admin.find({}, {_id: 1, name: 1, email: 1}).forEach(function (a) {
        admins[key(a._id)] = {name: a.name || '', email: a.email || ''};
    });
    db.site.find({}, {_id: 1, name: 1, desc: 1}).forEach(function (s) {
        sites[key(s._id)] = {name: s.name || '', desc: s.desc || ''};
    });
    db.privilege.find({}, {admin_id: 1, site_id: 1, role: 1}).forEach(function (p) {
        var aid = key(p.admin_id), sid = key(p.site_id);
        var a = admins[aid], s = sites[sid];
        if (!a || !s || !a.name) {
            throw new Error('Cannot resolve privilege associations: admin=' + aid + ' site=' + sid);
        }
        print(JSON.stringify({
            admin_id: aid,
            admin_name: a.name,
            admin_email: a.email,
            site_id: sid,
            site_name: s.name,
            site_description: s.desc,
            role: p.role
        }));
        count++;
    });
    if (count === 0 || count !== db.privilege.count()) throw new Error('Incomplete privilege export');
    print(JSON.stringify({_export_summary: true, privilege_count: count, admin_count: db.admin.count(), site_count: db.site.count()}));
}());
