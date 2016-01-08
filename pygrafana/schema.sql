drop table if exists dashboards;
create table dashboards (
  id        INTEGER primary key autoincrement,
  slug      STRING not null,
  dashboard TEXT   not null,
  isStarred BOOLEAN default 0 not null,
  created   TIMESTAMP default CURRENT_TIMESTAMP not null,
  updated   TIMESTAMP default CURRENT_TIMESTAMP not null,
  expires   TIMESTAMP default null
);

/* insert Home dashboard per default */
insert into dashboards (slug, dashboard) values ('home', '{"editable":true,"hideControls":true,"nav":[{"enable":false,"type":"timepicker"}],"rows":[{"collapse":false,"editable":true,"height":"100px","panels":[{"content":"\u003cdiv class=\"text-center\" style=\"padding: 10px 0 20px 0\"\u003e\n\u003cimg src=\"img/logo_transparent_200x.png\" width=\"170px\"\u003e \n\u003c/div\u003e","editable":true,"id":1,"mode":"html","span":12,"style":{},"title":"","type":"text"}],"title":"New row"},{"height":"610px","panels":[{"id":2,"mode":"starred","span":6,"title":"Starred dashboards","type":"dashlist"},{"id":3,"mode":"search","span":6,"title":"Dashboards","type":"dashlist"}]}],"style":"dark","tags":[],"templating":{"list":[]},"time":{"from":"now-6h","to":"now"},"timezone":"browser","title":"Home","version":1}');