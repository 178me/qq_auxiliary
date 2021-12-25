import cv2
import numpy as np


def edge_demo(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    #  cv2.imshow("input image", gray)
    #  cv2.waitKey(0)
    grad_x = cv2.Sobel(gray, cv2.CV_16SC1, 1, 0)
    #  cv2.imshow("input image", grad_x)
    #  cv2.waitKey(0)
    grad_y = cv2.Sobel(gray, cv2.CV_16SC1, 0, 1)
    #  cv2.imshow("input image", grad_y)
    #  cv2.waitKey(0)
    edge_output = cv2.Canny(grad_x, grad_y,  350,400)
    #  kernel = np.ones((2, 2), np.uint8)
    edge_output = cv2.dilate(edge_output, (2,2), iterations=1)
    cv2.imshow("input image", edge_output)
    cv2.waitKey(0)
    return edge_output


def contours_demo(image):
    binary = edge_demo(image)
    h,w = binary.shape
    print(w)
    lines = cv2.HoughLines(binary, 1, np.pi/180, int(w / 2),w)
    print(lines)
    for i in range(len(lines)):
        for rho,theta in lines[i]:
            a = np.cos(theta)
            b = np.sin(theta)
            x0 = a*rho
            y0 = b*rho
            x1 = int(x0 + w*(-b))
            y1 = int(y0 + w*(a))
            x2 = int(x0 - w*(-b))
            y2 = int(y0 - w*(a))
            print(x1,y1)
            print(x2,y2)
            cv2.line(binary,(x1,y1),(x2,y2),(0,255,255),2)
    #  cv2.imshow("lines", img)
    #  cv2.waitKey()
    #  cv2.imshow("lines", binary)
    #  cv2.waitKey()
    binary = cv2.dilate(binary, (5,5), iterations=1)
    contours, hierarchy = cv2.findContours(
        binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for i, contour in enumerate(contours):
        peri = cv2.arcLength(contour, True)
        print(peri)
        approx = cv2.approxPolyDP(contour, 0.02 * peri, True)
        print(len(approx))
        if len(approx) > 4:
            (x, y), radius = cv2.minEnclosingCircle(contour)
            print(x, y, radius)
            print()
            cv2.drawContours(image, [contour], -1, (0, 0, 255), 2)
            cv2.imshow("input image", image)
            cv2.waitKey(0)
        #  cv2.drawContours(image, contours, i, (0, 0, 255), 1)
        #  cv2.imshow("input image", image)
        #  cv2.waitKey(0)
    #  print(cX,cY)
    #  print(x,y)
    #  cv2.circle(image, (x, y), 2, (0, 0, 255), -1)


if __name__ == "__main__":
    img = cv2.imread("./src/ad5.png")
    contours_demo(img)
    cv2.imshow("input image", img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
