%% Four-wheel skid-steer kinematics - preliminary simulation
% Project: Vibration-aware autonomous mobile robot for fragile payloads
% Author: Nabhonil Sarkar
%
% This base-MATLAB model treats the front and rear wheels on each side as
% one coupled wheel pair. It compares ideal differential-drive kinematics
% with a provisional skid-steer correction that reduces yaw rate to account
% for lateral tyre scrub. The correction is an assumption, not a measured
% result, and must later be calibrated using experimental odometry data.

clear;
close all;
clc;

%% Output location
scriptFolder = fileparts(mfilename('fullpath'));
outputFolder = fullfile(scriptFolder, 'outputs');
if ~isfolder(outputFolder)
    mkdir(outputFolder);
end

%% Provisional robot geometry from the CAD concept
robot.chassisLength_m = 0.340;
robot.chassisWidth_m  = 0.270;
robot.wheelRadius_m   = 0.035;
robot.wheelWidth_m    = 0.028;

% The CAD parameter is 298 mm outside-to-outside. Subtracting one wheel
% width gives a provisional 270 mm centre-to-centre track width.
robot.trackWidth_m = 0.298 - robot.wheelWidth_m;

% Provisional front-to-rear axle spacing for the four-wheel layout.
robot.wheelbase_m = 0.250;

% eta = 1 is ideal no-slip differential-drive motion. A value below 1
% represents reduced turning response caused by four-wheel tyre scrub.
robot.turnEfficiency = 0.80;

%% Command sequence
dt = 0.02;
tEnd = 22;
t = (0:dt:tEnd).';
n = numel(t);

leftSpeed_mps  = zeros(n, 1);
rightSpeed_mps = zeros(n, 1);
phase = strings(n, 1);

for k = 1:n
    if t(k) < 4
        leftSpeed_mps(k)  = 0.25;
        rightSpeed_mps(k) = 0.25;
        phase(k) = "Straight 1";
    elseif t(k) < 8
        leftSpeed_mps(k)  = 0.12;
        rightSpeed_mps(k) = 0.28;
        phase(k) = "Left arc";
    elseif t(k) < 11
        leftSpeed_mps(k)  = -0.16;
        rightSpeed_mps(k) = 0.16;
        phase(k) = "Pivot left";
    elseif t(k) < 15
        leftSpeed_mps(k)  = 0.22;
        rightSpeed_mps(k) = 0.22;
        phase(k) = "Straight 2";
    elseif t(k) < 19
        leftSpeed_mps(k)  = 0.28;
        rightSpeed_mps(k) = 0.10;
        phase(k) = "Right arc";
    else
        leftSpeed_mps(k)  = 0;
        rightSpeed_mps(k) = 0;
        phase(k) = "Stop";
    end
end

%% Kinematic quantities
linearSpeed_mps = (rightSpeed_mps + leftSpeed_mps) / 2;
yawRateIdeal_radps = (rightSpeed_mps - leftSpeed_mps) / robot.trackWidth_m;
yawRateSkid_radps = robot.turnEfficiency * yawRateIdeal_radps;

% All four wheels are driven. Front and rear wheels on the same side use
% the same angular-speed command in this first-order kinematic model.
leftWheel_radps  = leftSpeed_mps / robot.wheelRadius_m;
rightWheel_radps = rightSpeed_mps / robot.wheelRadius_m;

%% Integrate ideal and provisional slip-adjusted paths
idealPose = integratePlanarPose(t, linearSpeed_mps, yawRateIdeal_radps);
skidPose  = integratePlanarPose(t, linearSpeed_mps, yawRateSkid_radps);

travelDistance_m = trapz(t, abs(linearSpeed_mps));
finalHeadingIdeal_deg = rad2deg(idealPose(end, 3));
finalHeadingSkid_deg  = rad2deg(skidPose(end, 3));

summary = table( ...
    robot.chassisLength_m, robot.chassisWidth_m, robot.wheelbase_m, ...
    robot.trackWidth_m, robot.wheelRadius_m, robot.turnEfficiency, ...
    max(abs(linearSpeed_mps)), max(abs(yawRateSkid_radps)), ...
    travelDistance_m, skidPose(end, 1), skidPose(end, 2), ...
    finalHeadingIdeal_deg, finalHeadingSkid_deg, ...
    'VariableNames', { ...
    'ChassisLength_m', 'ChassisWidth_m', 'Wheelbase_m', ...
    'TrackWidth_m', 'WheelRadius_m', 'TurnEfficiency', ...
    'MaximumLinearSpeed_mps', 'MaximumSkidYawRate_radps', ...
    'CommandedTravelDistance_m', 'FinalSkidX_m', 'FinalSkidY_m', ...
    'FinalIdealHeading_deg', 'FinalSkidHeading_deg'});

results = table(t, phase, leftSpeed_mps, rightSpeed_mps, ...
    leftWheel_radps, rightWheel_radps, linearSpeed_mps, ...
    yawRateIdeal_radps, yawRateSkid_radps, ...
    idealPose(:, 1), idealPose(:, 2), idealPose(:, 3), ...
    skidPose(:, 1), skidPose(:, 2), skidPose(:, 3), ...
    'VariableNames', {'Time_s', 'MotionPhase', 'LeftSideSpeed_mps', ...
    'RightSideSpeed_mps', 'LeftFrontRearWheelSpeed_radps', ...
    'RightFrontRearWheelSpeed_radps', 'LinearSpeed_mps', ...
    'IdealYawRate_radps', 'SkidAdjustedYawRate_radps', ...
    'IdealX_m', 'IdealY_m', 'IdealHeading_rad', ...
    'SkidX_m', 'SkidY_m', 'SkidHeading_rad'});

writetable(summary, fullfile(outputFolder, 'skid_steer_summary.csv'));
writetable(results, fullfile(outputFolder, 'skid_steer_timeseries.csv'));
save(fullfile(outputFolder, 'skid_steer_results.mat'), ...
    'robot', 't', 'phase', 'leftSpeed_mps', 'rightSpeed_mps', ...
    'linearSpeed_mps', 'yawRateIdeal_radps', 'yawRateSkid_radps', ...
    'idealPose', 'skidPose', 'summary', 'results');

%% Figure 1: trajectories
trajectoryFigure = figure('Color', 'w', 'Visible', 'off', ...
    'Position', [100 100 1100 720]);
plot(idealPose(:, 1), idealPose(:, 2), '--', 'Color', [0.15 0.40 0.75], ...
    'LineWidth', 2.0, 'DisplayName', 'Ideal no-slip model');
hold on;
plot(skidPose(:, 1), skidPose(:, 2), '-', 'Color', [0.85 0.33 0.10], ...
    'LineWidth', 2.5, 'DisplayName', ...
    sprintf('Provisional skid-steer model (eta = %.2f)', robot.turnEfficiency));
plot(skidPose(1, 1), skidPose(1, 2), 'o', 'MarkerSize', 9, ...
    'MarkerFaceColor', [0.20 0.65 0.30], 'MarkerEdgeColor', 'k', ...
    'DisplayName', 'Start');
plot(skidPose(end, 1), skidPose(end, 2), 's', 'MarkerSize', 9, ...
    'MarkerFaceColor', [0.70 0.20 0.20], 'MarkerEdgeColor', 'k', ...
    'DisplayName', 'Finish');

poseIndexes = round(linspace(1, n, 8));
for idx = poseIndexes
    drawRobotFootprint(skidPose(idx, :), robot, [0.85 0.33 0.10]);
end

axis equal;
grid on;
xlabel('Global x position (m)');
ylabel('Global y position (m)');
title({'Four-wheel skid-steer trajectory simulation', ...
    'Ideal kinematics compared with a provisional tyre-scrub correction'});
legend('Location', 'bestoutside');
exportgraphics(trajectoryFigure, ...
    fullfile(outputFolder, 'skid_steer_trajectory.png'), 'Resolution', 220);

%% Figure 2: command and motion profiles
profileFigure = figure('Color', 'w', 'Visible', 'off', ...
    'Position', [100 100 1200 850]);

subplot(3, 1, 1);
plot(t, leftSpeed_mps, 'Color', [0.15 0.40 0.75], 'LineWidth', 1.8);
hold on;
plot(t, rightSpeed_mps, 'Color', [0.85 0.33 0.10], 'LineWidth', 1.8);
grid on;
ylabel('Side speed (m/s)');
title('Commanded left- and right-side speeds');
legend('Left-front and left-rear', 'Right-front and right-rear', ...
    'Location', 'eastoutside');

subplot(3, 1, 2);
plot(t, leftWheel_radps, 'Color', [0.15 0.40 0.75], 'LineWidth', 1.8);
hold on;
plot(t, rightWheel_radps, 'Color', [0.85 0.33 0.10], 'LineWidth', 1.8);
grid on;
ylabel('Wheel speed (rad/s)');
title('Four-wheel angular-speed commands');
legend('Left pair', 'Right pair', 'Location', 'eastoutside');

subplot(3, 1, 3);
yyaxis left;
plot(t, linearSpeed_mps, 'Color', [0.20 0.60 0.35], 'LineWidth', 1.8);
ylabel('Linear speed (m/s)');
yyaxis right;
plot(t, yawRateIdeal_radps, '--', 'Color', [0.15 0.40 0.75], 'LineWidth', 1.5);
hold on;
plot(t, yawRateSkid_radps, '-', 'Color', [0.55 0.20 0.65], 'LineWidth', 1.8);
ylabel('Yaw rate (rad/s)');
grid on;
xlabel('Time (s)');
title('Robot linear speed and yaw response');
legend('Linear speed', 'Ideal yaw rate', 'Skid-adjusted yaw rate', ...
    'Location', 'eastoutside');

sgtitle('Preliminary four-wheel skid-steer kinematic results');
exportgraphics(profileFigure, ...
    fullfile(outputFolder, 'skid_steer_motion_profiles.png'), 'Resolution', 220);

%% Console report
fprintf('\nFour-wheel skid-steer simulation complete.\n');
fprintf('Track width: %.3f m\n', robot.trackWidth_m);
fprintf('Wheel radius: %.3f m\n', robot.wheelRadius_m);
fprintf('Provisional turn efficiency: %.2f\n', robot.turnEfficiency);
fprintf('Commanded travel distance: %.3f m\n', travelDistance_m);
fprintf('Final skid-adjusted pose: x = %.3f m, y = %.3f m, heading = %.1f deg\n', ...
    skidPose(end, 1), skidPose(end, 2), finalHeadingSkid_deg);
fprintf('Results saved to: %s\n\n', outputFolder);

%% Local functions
function pose = integratePlanarPose(t, linearSpeed, yawRate)
    pose = zeros(numel(t), 3);
    for k = 2:numel(t)
        dtLocal = t(k) - t(k - 1);
        thetaMid = pose(k - 1, 3) + 0.5 * yawRate(k - 1) * dtLocal;
        pose(k, 1) = pose(k - 1, 1) + ...
            linearSpeed(k - 1) * cos(thetaMid) * dtLocal;
        pose(k, 2) = pose(k - 1, 2) + ...
            linearSpeed(k - 1) * sin(thetaMid) * dtLocal;
        pose(k, 3) = pose(k - 1, 3) + yawRate(k - 1) * dtLocal;
    end
end

function drawRobotFootprint(pose, robot, edgeColour)
    halfLength = robot.chassisLength_m / 2;
    halfWidth = robot.chassisWidth_m / 2;
    localCorners = [ halfLength,  halfWidth; ...
                     halfLength, -halfWidth; ...
                    -halfLength, -halfWidth; ...
                    -halfLength,  halfWidth; ...
                     halfLength,  halfWidth];
    rotation = [cos(pose(3)), -sin(pose(3)); ...
                sin(pose(3)),  cos(pose(3))];
    globalCorners = (rotation * localCorners.').';
    globalCorners(:, 1) = globalCorners(:, 1) + pose(1);
    globalCorners(:, 2) = globalCorners(:, 2) + pose(2);
    lightEdgeColour = 0.60 * edgeColour + 0.40 * [1 1 1];
    plot(globalCorners(:, 1), globalCorners(:, 2), '-', ...
        'Color', lightEdgeColour, 'LineWidth', 0.9, ...
        'HandleVisibility', 'off');
end
