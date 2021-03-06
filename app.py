from flask import Flask, jsonify, render_template, redirect, url_for, make_response, request, escape, session
import MySQLdb
import lib.Users as Users
import lib.Friends as Friends
import lib.Neighbors as Neighbors
import lib.Search as Search
import lib.Block as Block
import lib.message_boards as message_boards
import lib.Threads as Threads
# from flask.ext.session import Session
from lib import Hood

app = Flask(__name__)
# Session(app)
app.config.from_pyfile("config.conf", silent=False)


class DB:
    conn = None

    def connect(self):
        self.conn = MySQLdb.connect(
            host=app.config.get("DATABASE_HOST"),
            user=app.config.get("DATABASE_USER"),
            # passwd=app.config.get("DATABASE_HOST"),
            db=app.config.get("DATABASE_DB")
        )
        self.conn.autocommit(False)
        self.conn.set_character_set('utf8')

    def query(self, sql, args=None):
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, args)
            # commit
        except (AttributeError, MySQLdb.OperationalError):
            self.connect()
            cursor = self.conn.cursor()
            cursor.execute(sql, args)
        return cursor

    def createSession(self, uid):
        session['uid'] = uid


if __name__ == "__main__":
    app.secret_key = app.config.get("SECRET_KEY")
    print("app secret key:", app.secret_key)
    db = DB()  # creating db connection
    db.connect()
    notifications = None


# @app.route("/")
# def hello():
#    return "Hello World!"

@app.route("/")
def index():
    message = None
    if 'uid' in session:
        # logging.info(session)
        print("on home page")
        return redirect(url_for('show_feed'))  # user feed html

    return render_template('index.html', session=session, message=message)


@app.route("/users/login", methods=['GET', 'POST'])
def login():
    message = None
    global notifications
    if notifications:
        message = notifications
        notifications = None
    if 'uid' in session:
        return redirect(url_for('show_feed'))
    print("Inside login")
    if request.method == 'POST':
        result = Users.getUser(db, request.form)
        print(result)
        if not result:
            notifications = {'message': 'Logged in', 'type': 'success'}
            # XSS Protection
            # response = make_response(render_template('user-feed.html', message=message))
            # response.headers['X-XSS-Protection'] = '1; mode=block'
            # return redirect('show_feed.html', message=message)
            return redirect(url_for('show_feed'))
        else:
            message = {'message': 'Failed to log in', 'type': 'error'}
            # response = make_response(render_template('login.html', message=message))
            # response.headers['X-XSS-Protection'] = '1; mode=block'
            return render_template('login.html', message=message)
    # response = make_response(render_template('login.html', message=message))
    # response.headers['X-XSS-Protection'] = '1; mode=block'
    else:
        return render_template('login.html', message=message)


@app.route('/logout')
def logout():
    global notifications
    print("in logout")
    if 'uid' not in session:
        return redirect(url_for('login'))
    result = Users.logout(db.conn)
    print("result:", result)
    if not result:
        session.pop('uid', None)
        notifications = {'message': 'Logged out', 'type': 'success'}
        return redirect(url_for('login'))
    else:
        message = {'message': 'Logout failed', 'type': 'error'}
        return message


@app.route("/users/signup", methods=['GET', 'POST'])
def signup():
    notifications = None
    message = None
    if request.method == 'POST':
        print(db.conn)

        result = Users.signup(db, db.conn, request.form, app.config.get("PWD_ROUNDS"))
        if not result:
            print("in signup success result")
            notifications = {'message': 'Registration successful', 'type': 'success'}
            result = Hood.getHooddetails(db.conn)
            return render_template('join_block.html', hoodinfo=result, notifications=notifications)
        else:
            print("in signup error")
            message = {'message': 'Something went wrong: ' + result, 'type': 'error'}
            return render_template('sign-up.html', message=message)
    else:
        print("in signup get call")
        return render_template('sign-up.html', message=message)


@app.route("/users/update_password", methods=['POST'])
def update_password():
    notifications = None
    message = None
    print ("in app.py update password");
    result = Users.update_password(db.conn, request.form)
    if not result:
        notifications = {'message': 'Password updated', 'type': 'success'}
        print("in app.py update password successful")
        return render_template('edit_profile.html', message=message)
    else:
        notifications = {'message': 'Something went wrong: ' + result, 'type': 'error'}
        return render_template('edit_profile.html',notifications=notifications)


@app.route("/users/update_block_details", methods=['POST'])
def update_block_details():
    notifications = None
    result = Users.update_block_details(db.conn, None)
    if not result:
        notifications = {'message': 'Block details updated', 'type': 'success'}
        return notifications
    else:
        notifications = {'message': 'Something went wrong: ' + result, 'type': 'error'}
        return notifications


@app.route("/users/update_profile", methods=['POST'])
def update_profile():
    notifications = None
    result = Users.update_profile_details(db.conn, None)
    if not result:
        notifications = {'message': 'Profile details updated', 'type': 'success'}
        return notifications
    else:
        notifications = {'message': 'Something went wrong: ' + result, 'type': 'error'}
        return notifications


@app.route("/users/view_profile", methods=['GET'])
def view_profile():
    notifications = None
    if 'uid' not in session:
        return redirect(url_for('login'))
    result = Users.view_profile(db.conn, None)
    if not result:
        message = {'message': 'User doesnot exist', 'type': 'success'}
        # return notifications
        redirect(url_for('login'))
    else:
        message = result
        return render_template('show_profile.html', message=message)


## add friend api
@app.route("/friends/send_friend_request", methods=['GET', 'POST'])
def send_friend_request():
    notifications = None
    if request.method == "GET":
        friendid = request.args.get('userid')
        print("friend id from ui is:", friendid)
        result = Friends.send_friend_request(db.conn, friendid)
        if not result:
            message = {'message': 'Friend Request sent', 'type': 'success'}
            # return notifications
            return render_template('show-people.html', message=message)
        else:
            message = {'message': 'Failed to send request.Please try again!', 'type': 'error'}
            return render_template('show-people.html', message=message)
            # return message
    else:
        return render_template('show-people.html')


@app.route("/friends/accept_friend_request", methods=['GET', 'POST'])
def accept_friend_request():
    notifications = None
    if request.method == "GET":
        friendid = request.args.get('userid')
        action = request.args.get('action')
        result = Friends.accept_friend_request(db.conn, friendid, action)
        if not result:
            message = {'message': 'Friend request accepted', 'type': 'success'}
            return render_template('friend-requests.html', message=message)
        else:
            message = {'message': 'Failed to send request.Please try again!', 'type': 'error'}
            return render_template('friend-requests.html', message=message)
    else:
        return render_template('friend-requests.html')


@app.route("/neighbors/send_block_request", methods=['GET', 'POST'])
def send_block_request():
    notifications = None
    message = None
    print("in block request UI call")
    if 'uid' not in session:
        print("session in accept request", session)
        return redirect(url_for('login'))
    if request.method == 'POST':
        print("in block request call")
        result = Neighbors.block_request(db.conn, request.form)
        if not result:
            print("in join block request success call")
            notifications = {'message': 'Neighborhood request sent', 'type': 'success'}
            return render_template("user-feed.html", notifications=notifications)
        else:
            print("in join block request failure call")
            message = {'message': 'Failed to send request.Please try again!', 'type': 'error'}
            return render_template("join_block.html", message=message)
    else:
        print("in join block get call")
        return render_template("join_block.html", message=message)


# get friends of a user

@app.route("/friends/get_friends_details", methods=['GET', 'POST'])
def get_friends_details():
    notifications = None
    if request.method == "GET":
        result = Friends.get_friend_requests(db.conn)
        if not result:
            message = {'message': 'Error in fetching', 'type': 'success'}
            return render_template("friend-requests.html", message=message)
        else:
            friendDetails = result
            return render_template("friend-requests.html", friendDetails=friendDetails)
    else:
        print("in else")
        return render_template('friend-requests.html')


@app.route("/neighbors/approve_block_request", methods=['GET', 'POST'])
def accept_block_request():
    notifications = None
    if request.method == "GET":
        id = request.args.get('userid')
        print("usrid is:", id)
        result = Neighbors.block_approve(db.conn, id)
        if not result:
            message = {'message': 'Failed to send request.Please try again!', 'type': 'error'}
            # return notifications
            return render_template("approval-requests.html", message=message)
        else:
            details = result
            message = {'message': 'Neighborhood request approved', 'type': 'success'}
            return render_template("approval-requests.html", details=details)
    else:
        return render_template("approval-requests.html")


@app.route("/neighbors/get_blockapproval_requests", methods=['GET', 'POST'])
def get_blockapproval_requests():
    notifications = None
    if request.method == "GET":
        result = Neighbors.get_requests_for_block(db.conn)
        if not result:
            message = {'message': 'Failed to send request.Please try again!', 'type': 'error'}
            # return notifications
            return render_template("approval-requests.html", message=message)
        else:
            details = result
            message = {'message': 'Neighborhood request approved', 'type': 'success'}
            return render_template("approval-requests.html", details=details)
    else:
        return render_template("approval-requests.html")


@app.route("/neighbors/leave_block", methods=['GET', 'POST'])
def leave_block():
    notifications = None
    result = Neighbors.leave_block(db.conn, None)
    if not result:
        notifications = {'message': 'Block left.Please update your new block!', 'type': 'success'}
        return notifications
    else:
        message = {'message': 'Failed to send request.Please try again!', 'type': 'error'}
        return message


##add neighbors
@app.route("/neighbors/add_neighbors", methods=['GET', 'POST'])
def add_neighbors():
    notifications = None
    message=None
    if request.method == "GET":
        neighborid = request.args.get('userid')
        result = Neighbors.add_neighbors(db.conn, neighborid)
        if not result:
            message = {'message': 'Neighbors added successfully!', 'type': 'success'}
            return render_template("show-people.html", message=message)
            # return notifications
        else:
            message = {'message': 'Failed to send request.Please try again!', 'type': 'error'}
            # return message
            return render_template("show-people.html", message=message)
    else:
        return render_template("show-people.html", message=message)


@app.route("/search/people", methods=['GET', 'POST'])
def search_people():
    notifications = None
    if request.method == 'POST':
        print("in search people")
        result = Search.search_people(db.conn, request.form)
        if not result:
            message = {'message': 'Search failed', 'type': 'failure'}
            return render_template("user-feed.html", message=message)
        else:
            # notifications = result
            print("result is:", result)
            return render_template("show-people.html", people=result)
    else:
        return render_template("show-people.html", notifications=notifications)


@app.route("/search/thread", methods=['GET', 'POST'])
def search_threads():
    notifications = None
    result = [{}]
    if request.method == 'POST':
        print("in search thread")
        result = Search.search_thread(db.conn, request.form)
        if not result:
            message = {'message': 'Search failed', 'type': 'failure'}
            return render_template("user-feed.html", message=message)
        else:
            # notifications = result
            print("result is:", result)
            return render_template("show-threads.html", threads=result)
    else:
        return render_template("show-threads.html", notifications=notifications)


@app.route('/feed', methods=['GET', 'POST'])
def show_feed():
    print("in show feed")
    if 'uid' not in session:
        print(session)
        return redirect(url_for('login'))
    # db = DB()
    if request.method == 'GET':
        # friend
        friendThreads = message_boards.getUserFriendThreads(db, latest=True)
        # logging.info(friendThreads)
        friendThreadInfo = []
        if friendThreads is not None:
            for ft in friendThreads:
                # logging.info(ft)
                threadDeets = message_boards.getThreadDetails(db, ft, '0')
                if threadDeets:
                    friendThreadInfo.append(
                        {'tid': threadDeets[0], 'CreatedBy': threadDeets[1], 'Title': threadDeets[2],
                         'Description_Msg': threadDeets[3], 'CreatedAt': threadDeets[4]})
        print(friendThreadInfo)

        # Neighbors
        neighborThreads = message_boards.getUserNeighborThreads(db, latest=True)
        neighborThreadInfo = []
        if neighborThreads is not None:
            # logging.info(neighborThreads)
            for nt in neighborThreads:
                # logging.info(nt)
                threadDeets = message_boards.getThreadDetails(db, nt, '1')
                # logging.info(threadDeets)
                if threadDeets:
                    neighborThreadInfo.append(
                        {'tid': threadDeets[0], 'CreatedBy': threadDeets[1], 'Title': threadDeets[2],
                         'Description_Msg': threadDeets[3], 'CreatedAt': threadDeets[4]})
        print(neighborThreadInfo)

        # block
        blockThreads = message_boards.getUserBlockThreads(db, latest=True)
        blockThreadInfo = []
        if blockThreads is not None:
            # logging.info(blockThreads)
            # blockThreadInfo = []
            for bt in blockThreads:
                # logging.info(bt)
                threadDeets = message_boards.getThreadDetails(db, bt, '2')
                if threadDeets:
                    blockThreadInfo.append({'tid': threadDeets[0], 'CreatedBy': threadDeets[1], 'Title': threadDeets[2],
                                            'Description_Msg': threadDeets[3], 'CreatedAt': threadDeets[4]})
        print(blockThreadInfo)

        # hood
        hoodThreads = message_boards.getUserHoodThreads(db, latest=True)
        hoodThreadInfo = []
        if hoodThreads is not None:
            # logging.info("hood threads")
            # logging.info(hoodThreads)
            # hoodThreadInfo = []
            for ht in hoodThreads:
                threadDeets = message_boards.getThreadDetails(db, ht, '3')
                # logging.info("HOOD threadDeets")
                # logging.info(threadDeets)
                if threadDeets:
                    hoodThreadInfo.append({'tid': threadDeets[0], 'CreatedBy': threadDeets[1], 'Title': threadDeets[2],
                                           'Description_Msg': threadDeets[3], 'CreatedAt': threadDeets[4]})
        print(hoodThreadInfo)
        return render_template('user-feed.html', friendFeedInfo=friendThreadInfo, neighborFeedInfo=neighborThreadInfo,
                               blockFeedInfo=blockThreadInfo, hoodFeedInfo=hoodThreadInfo)

    if request.method == 'POST':
        print("in post feed")
        if request.form['submit_btn'] == 'submit':
            print(" flow")
            result = message_boards.postNewThread(db, request.form)
        # logging.info(result)
    return render_template('user-feed.html')


# TODO : XSS
@app.route('/block-feed', methods=['GET', 'POST'])
def blockfeed():
    # logging.info("Fetching block feed")
    # get thread description
    blockThreads = message_boards.getUserBlockThreads(db)
    blockThreads = list(set(blockThreads))
    # logging.info(blockThreads)
    blockThreadInfo = []
    for bt in blockThreads:
        # logging.info(bt)
        threadDeets = message_boards.getThreadDetails(db, bt, '2')
        if threadDeets:
            blockThreadInfo.append({'tid': threadDeets[0], 'CreatedBy': threadDeets[1], 'Title': threadDeets[2],
                                    'Description_Msg': threadDeets[3], 'CreatedAt': threadDeets[4]})

    return render_template('block_feed.html', blockFeedInfo=blockThreadInfo)


# TODO : Populate the thread details on top
@app.route('/show-thread', methods=['GET', 'POST'])
def showThread():
    # logging.info('get thread')
    if 'uid' not in session:
        #logging.info(session)
        return redirect(url_for('login'))
    #logging.info('get thread')
    commentInfo = []
    if request.method == 'GET':
        tid = request.args.get('tid')
        #logging.info('getting full thread')
        #logging.info(tid)
        commentInfo = []
        comments = message_boards.showThreadComments(db, tid)
        #logging.info(comments)
        # get thread title
        title = message_boards.getThreadTitle(db, tid)
        for c in comments:
            if comments:
                commentInfo.append({'tid': c[0], 'comment': c[1], 'tid': c[2], 'FName': c[3], 'LName': c[4]})
        #logging.info("rendering template")
        # return jsonify({'threadCommentInfo' : commentInfo, 'threadTitle' : title})
        return render_template('thread-details.html', threadCommentInfo=commentInfo, threadTitle=title, tid=tid)
    if request.method == 'POST':
        #logging.info(request)
        print('post comment on thread ')
        tid = request.args.get('tid')
        posted = message_boards.postComment(db, request.form, tid)
        if posted is None:
            print('Posted comment successfully')
            message = {'message': 'Posted comment successfully', 'type': 'success'}
            # get thread title
            title = message_boards.getThreadTitle(db, tid)
            comments = message_boards.showThreadComments(db, tid)
            for c in comments:
                if comments:
                    commentInfo.append(
                        {'tid': c[0], 'comment': c[1], 'commentTime': c[2], 'FName': c[3], 'LName': c[4]})
            response = make_response(
                render_template('thread-details.html', threadCommentInfo=commentInfo, threadTitle=title, message=message,
                                tid=tid))
            response.headers['X-XSS-Protection'] = '1; mode=block'
            return response
        else:
            message = {'message': 'Error in posting comment', 'type': 'error'}
            response = make_response(render_template("thread-details.html", message=message))
            response.headers['X-XSS-Protection'] = '1; mode=block'
            return response


@app.route('/hood-feed', methods=['GET', 'POST'])
def hoodfeed():
    # logging.info("Fetching hood feed")
    hoodThreads = message_boards.getUserHoodThreads(db)
    # logging.info("hood threads")
    hoodThreads = list(set(hoodThreads))
    # logging.info(hoodThreads)
    hoodThreadInfo = []
    for ht in hoodThreads:
        # logging.info("getting hood thread deets")
        threadDeets = message_boards.getThreadDetails(db, ht, '3')
        if threadDeets:
            hoodThreadInfo.append({'tid': threadDeets[0], 'CreatedBy': threadDeets[1], 'Title': threadDeets[2],
                                   'Description_Msg': threadDeets[3], 'CreatedAt': threadDeets[4]})

    return render_template('hood_feed.html', hoodFeedInfo=hoodThreadInfo)


@app.route('/friend-feed', methods=['GET', 'POST'])
def friendfeed():
    # logging.info("Fetching friend feed")
    friendThreads = message_boards.getUserFriendThreads(db)
    # logging.info(friendThreads)
    friendThreadInfo = []
    for ft in friendThreads:
        # logging.info(ft)
        threadDeets = message_boards.getThreadDetails(db, ft, '0')
        if threadDeets:
            friendThreadInfo.append({'tid': threadDeets[0], 'CreatedBy': threadDeets[1], 'Title': threadDeets[2],
                                     'Description_Msg': threadDeets[3], 'CreatedAt': threadDeets[4]})
    # logging.info(friendThreadInfo)
    return render_template('friend_feed.html', friendFeedInfo=friendThreadInfo)


@app.route('/neighbor-feed', methods=['GET', 'POST'])
def neighborfeed():
    # logging.info("Fetching neighbor feed")
    neighborThreads = message_boards.getUserNeighborThreads(db)
    # logging.info(neighborThreads)
    neighborThreadInfo = []
    for nt in neighborThreads:
        # logging.info(nt)
        threadDeets = message_boards.getThreadDetails(db, nt, '1')
        # logging.info(threadDeets)
        if threadDeets:
            neighborThreadInfo.append({'tid': threadDeets[0], 'CreatedBy': threadDeets[1], 'Title': threadDeets[2],
                                       'Description_Msg': threadDeets[3], 'CreatedAt': threadDeets[4]})
    # logging.info(neighborThreadInfo)
    return render_template('neighbor_feed.html', neighborFeedInfo=neighborThreadInfo)


@app.route('/threads')
def show_message():
    if 'uid' not in session:
        return redirect(url_for('login'))
    allInfo = message_boards.getUserThreads(db)
    return render_template('show-threads.html', allInfo=allInfo)


@app.route('/profile')
def profile():
    if 'uid' not in session:
        return redirect(url_for('login'))
    block_name="approval_pending"
    profile = []
    if request.method == 'GET':
        profile_data = Users.view_profile(db.conn, request.form)
        block_id = profile_data[14]
        if block_id is not None:
            block_name = Block.getBlockNameFromBid(db, block_id)
        if profile_data:
            profile.append({"Fname": profile_data[1], "LName": profile_data[2], "email": profile_data[3],
                            "apt": profile_data[5],
                            "street": profile_data[6], "city": profile_data[7], "state": profile_data[8],
                            "zip": profile_data[9], "block_name": block_name, "email_preference": profile_data[14]})
    return render_template('show_profile.html', profileInfo=profile)


@app.route('/block_details', methods=['GET', 'POST'])
def get_block_details():
    if request.method == "POST":
        result = Block.get_block_details(db.conn, request.form)
        return render_template('join_block.html', blockinfo=result)
    else:
        message = {'message': 'Failed to send request.Please try again!', 'type': 'error'}
        return render_template('join_block.html', message=message)


@app.route('/neighborhood_details')
def get_neighborhood_details():
    # if request.method == "POST":
    notifications = {}
    result = Hood.getHooddetails(db.conn)
    return render_template('join_block.html', hoodinfo=result, notifications = notifications)


# else:
#     message={'message': 'Failed to send request.Please try again!', 'type': 'error'}
#     return render_template('join_block.html', message=message)

@app.route('/searchMessages')
def getSearchMessagesPage():
    message = {}
    print("in serach message")
    return render_template('search-threads.html', message=message)


@app.route('/searchPeople')
def getSearchPeoplePage():
    message = {}
    return render_template('search-people.html', message=message)


@app.route('/blockaprrovalrequests')
def getBlockApprovalRequests():
    message = {}
    return render_template('approval-requests.html', message=message)


@app.route('/block_details_for_hood', methods=['GET', 'POST'])
def block_details_for_hood():
    if request.method == "GET":
        hoodid = request.args.get('selectedHoodid');
        blockList = Block.get_block_details_for_hood(db.conn, hoodid)
        return jsonify(blockList=blockList);
        #print("block list returned:",blockList)
        #return blockList
    else:
        message = {'message': 'Failed to send request.Please try again!', 'type': 'error'}
        return render_template('join_block.html', message=message)


@app.route('/changePasswordPage')
def getChangePasswordHTML():
    message = {}
    return render_template('change_password.html', message=message)


@app.route('/updateProfilePage')
def getUpdateProfileHTML():
    message = {}
    print(request.form);
    return render_template('edit_profile.html', info=request.form)

@app.route('/show-thread/post-comment', methods=['POST'])
def postThreadComment():
    if 'uid' not in session:
        # logging.info(session)
        return redirect(url_for('login'))
    if request.method == 'POST':
        # logging.info('post comment on thread ')
        posted = message_boards.postComment(db.conn, request.form)
        if posted is None:
            message = {'message': 'Posted comment successfully', 'type': 'success'}
            response = make_response(render_template("show-threads.html", message=message))
            response.headers['X-XSS-Protection'] = '1; mode=block'
            return response
        else:
            message = {'message': 'Error in posting comment', 'type': 'error'}
            response = make_response(render_template("show-threads.html", message=message))
            response.headers['X-XSS-Protection'] = '1; mode=block'
            return response


@app.route('/create-new-thread', methods=['POST'])
def createNewThread():
    if 'uid' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        print("app.py create thread");
        print(request.form["privacy"])
        thread = message_boards.postNewThread(db.conn, request.form)
        if thread is None:
            message = {'message' : 'Thread created successfully', 'type' : 'success'}
            return message
        else:
            message = {'message': 'Error in creating thread', 'type': 'error'}
            return message

@app.route('/map-view-friends')
def getMapViewForFriends():
    message = {}
    return render_template('map_friends.html', message = message);

@app.route('/map-view-threads')
def getMapViewForThreads():
    message = {}
    return render_template('map_threads.html', message = message);

@app.route('/map-view-neighbors')
def getMapViewForNeighbors():
    message = {}
    return render_template('map_neighbors.html', message = message);

if __name__ == "__main__":
    app.run()
