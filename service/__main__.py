import bottle

from config_finder import cfg

from m2.handlers import handle_build

from handlers import (
    handle_branch_commit as leg_handle_branch_commit,
    handle_build as leg_handle_build,
)

from security import restricted

### v1 paths ###
# regex   [^\/]+\/?                    [^\/]+     (\/?[^\/]+)?
#         path followed by a slash     path       optional slash and path
v1_build_path = "/v1/build/<service_name>/<branch_name>/<commit_hash>" + \
                         "/<image_name:re:[^\/]+\/?[^\/]+(\/?[^\/]+)?>"

bottle.route(build_path, ["GET"], restricted(handle_build))

### legacy paths ###
leg_commit_path = "/commit/<{}>/<{}>/<{}>/<{}>".format(
    "repo_name",
    "feature_name",
    "branch_name",
    "commit_hash",
)

# regex   [^\/]+\/?                    [^\/]+     (\/?[^\/]+)?
#         path followed by a slash     path       optional slash and path
leg_build_path = "/build/<commit_hash>/<image_name:re:[^\/]+\/?[^\/]+(\/?[^\/]+)?>"

bottle.route(leg_commit_path, ["GET"], restricted(leg_handle_branch_commit))
bottle.route(leg_build_path, ["GET"], restricted(leg_handle_build))

debug = cfg("debug", "false") == "true"
print("running herd api, debug? {}".format(debug))
bottle.run(host="0.0.0.0", port="8000", debug=debug)
