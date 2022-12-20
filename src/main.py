"""
This script is for estimating the HTTP traffic capacity for a web server.
It can be ran from terminal using the args:
--rps=<target requests per second>
--url=<web server URL>

Example:
python3 script.py --url=http://localhost:3000/ --rps=400
"""
import argparse
import threading
import time
import requests


class HttpTest:
    """
    HttpTest is a class that manages the threads and connections
    to the web server.
    The two arguments passed are:
    url --> the web server host, e.g., http://localhost:3000
    target_rps --> the target requests per second, e.g., 100
    """
    def __init__(self, url: str, target_rps: int):
        self.total_requests = 0
        self.url = url
        self.target_rps = target_rps  # Desired requests per second
        self.rps = 0
        self.running = False

        self.headers = {
            "User-Agent": "Mozilla/5.0 (platform; rv:geckoversion) \
                Gecko/geckotrail Firefox/firefoxversion"
        }

    @classmethod
    def timer(cls):
        """
        Returns a perfect time counter, this is used to calculate
        how many requests are being sent per second.
        """
        return time.perf_counter()

    def test_request(self, req_count):
        """
        Returns the average time taken for n number of requests specified by
        req_count arg.
        """
        timings = []
        request_count = req_count

        while len(timings) < request_count:
            start_time = self.timer()
            if requests.get(self.url).status_code == 200:
                timings.append(self.timer() - start_time)
        return sum(timings) / len(timings)

    def get_request(self):
        """
        get_request is an important part of the class, it is used for sending
        the requests to the server and is aimed to be executed in a thread
        which allows multiple instances of it to run at once. The targetted
        web server host URL is specified when the class is created so no new
        arguments are required.

        Every time the web server returns a status code of 200 (successful request),
        a request is added to the total_requests variable to allow for the requests
        per second calculation.

        If the status code returned is not 200, the function will increment the
        error_count variable, which after 3 attempts will finish and return the
        execution of the function code in the thread.
        """
        error_count = 0

        while self.running:
            if requests.get(self.url, headers=self.headers).status_code == 200:
                self.total_requests += 1
            else: error_count += 1

            if error_count > 2:
                return

    def request_manager(self):
        """
        Creates and manages the desired amount of requests at the targetted
        web server by utilising threading.

        The test_request method is utilised to determine the average time
        for a request so that the thread count needed to reach the target
        requests per second specified.
        """
        self.running = True  # All threads will quit if this is set to False

        average_request_time = self.test_request(10) 
        print(f"Average Request Time: {average_request_time}")

        max_req_thread = round(1 / average_request_time)
        thread_count = round(self.target_rps / max_req_thread)
        print(f"Thread Count: {thread_count}")

        request_threads = []

        for thread in range(thread_count):
            request_threads.append(threading.Thread(target=self.get_request))
        for thread in request_threads:
            thread.start()

        current_req_count = 0
        time_slept = 0.5

        print("Press Ctrl + C to exit\n\n")
        try:
            while True:
                previous_total_requests = current_req_count

                time.sleep(time_slept)
                current_req_count = self.total_requests
                self.rps = (current_req_count - previous_total_requests) / time_slept
                print(f"Requests per second: {self.rps} / {self.target_rps} ", end="\r")
        except KeyboardInterrupt:
            self.running = False
            for thread in request_threads:
                thread.join()
            print("\nQuitting...")


def main():
    """ main function """
    parser = argparse.ArgumentParser()
    parser.add_argument("--rps", type=int, required=True, help="Target number of requests per second")
    parser.add_argument("--url", type=str, required=True, help="The full URL for testing")
    args = parser.parse_args()

    print(f"Target requests/second: {args.rps}")
    print(f"Target website: {args.url}")

    strain_test = HttpTest(args.url, args.rps)
    strain_test.request_manager()



if __name__ == "__main__":
    main()
